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

WHAT THOSE ARMS PROVE, STATED EXACTLY. Each one IMPORTS the module it
represents, resolves that module's redacting class by name out of it, and
builds an instance whose withheld field holds the planted token - so the repr
that runs and is bypassed is the SHIPPED one. The previous spelling generated a
stand-in class with no imports, which measured a property of pytest's rewriter
rather than anything about the module it was named after; an arm that cannot
reach its shipped class now raises before its assertion and is caught by
``test_every_forced_arm_reached_its_assertion_through_shipped_construction``
rather than passing quietly. What the arms still do NOT execute is the shipped
module's own assertions: four of the covered modules ship the redacting class
and no assertion at all, so there is no arm of theirs to force.

NO ARM IS SKIPPED, AND THERE IS EXACTLY ONE ALLOWANCE, named here because an
unstated one is the kind that rots. ``REPR_RAISING_HOLDERS`` records the shipped
classes whose own ``__repr__`` RAISES while an arm holds a planted value in the
field it reads. Those arms still run and still measure what they are for -
saferepr replaces the RECEIVER's rendering only, so the planted value still
reaches the report - and the record is asserted in BOTH directions by
``test_the_shipped_repr_is_what_gets_bypassed_in_every_forced_arm``: a new class
that starts raising reddens, and an entry whose class has stopped raising
reddens too. It is an allowance that cannot become silent, not an exemption.

THREE SANDBOXES AND EACH IS LOAD-BEARING. The FLOOR runs the same arms with the
comparison unforced and must be green, which is what separates "the forcing
worked" from "every arm errored in construction" - two states with the same
exit code. The CONTROL forces them and must render every planted token. The
REMEDIED run forces them with the aggregate bound to a scalar first and must
render none, and each of its arms is separately measured to have reached its
own assertion, or a clean grep would be satisfied by ten arms that never ran.

Three token classes are planted - a save-derived name, a home path and an
account directory - and
``test_every_sensitive_class_is_covered_by_the_forced_arms`` asserts all three
are actually exercised rather than merely defined. Each arm's token is UNIQUE,
because ten arms sharing three tokens made the grep a pooled threshold that one
arm could satisfy on another's behalf.

THE SECOND CHANNEL IS GRADED TOO, at the foot of this module. pytest renders
the failing function's own source lines - measured: its docstring once, its
comments once, a module-scope binding zero times, a line below the failing one
zero times - so a value written literally into a function body reaches the
report without the rewriter touching it. That sweep reaches two of the three
classes, and which one it cannot reach is measured rather than hedged.

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

THE ENVIRONMENT IS GRADED HERE TOO, BY SOURCE RATHER THAN BY DECLARATION.
``os.environ`` ships no withholding ``__repr__``, so it sits outside the
declaration-derived population above by construction. CS-1199 grades it as a
named source instead, in the section at the foot of this module.

THE MARKERS ARE SYNTHETIC AND THE MACHINE'S ARE NEVER PRINTED. Every planted
token below is invented. The one place this module touches real machine state -
the redactor measurement - derives its spellings at run time and reports a
verdict rather than a value.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from types import MappingProxyType
from typing import Final, NamedTuple

import pytest

from clockspeed.data.locate import SAVE_ROOT_PARTS
from tests import assertion_rendering_guard as guard
from tests.assertion_rendering_guard import (
    ANY_FUNCTION,
    CONTENT_REDUCERS,
    CONTENT_TRANSPARENT,
    ECHO_ACCOUNT,
    ECHO_HOME,
    ECHO_MACHINE,
    ELEMENT_REDUCERS,
    LIBRARY_LOCATORS,
    MEASURE_REDUCERS,
    REACH_PRIMITIVES,
    Finding,
    describe,
    describe_echoes,
    explained,
    rendered_parts,
    scan_repo,
    scan_repo_source_echoes,
    scan_source,
    scope_statements,
    source_echoes,
    tracked_python_files,
)
from tests.conftest import REDACTED_HOME, REDACTED_USER, redact_personal_data
from tests.save import reach_guard

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
SUBPROCESS_TIMEOUT: Final = 300

#: pytest's exit code when tests ran and at least one of them failed.
PYTEST_TESTS_FAILED: Final = 1

#: pytest's exit code when every test ran and passed.
PYTEST_ALL_PASSED: Final = 0

#: The separator pytest writes between a rendered value and the expression it
#: came from, in the `where <value> = <expression>` explanation chain.
RENDERED_EQUALS: Final = " = "

#: What pytest's saferepr writes in place of a repr that raised.
REPR_RAISED_MARKER: Final = "raised in repr()"

#: Shipped classes whose own ``__repr__`` cannot fire while a forced arm holds
#: a planted value in the field that repr reads, with the reason for each.
#:
#: RECORDED IN BOTH DIRECTIONS by
#: ``test_the_shipped_repr_is_what_gets_bypassed_in_every_forced_arm``: a
#: second class that starts raising reddens, and an entry whose class has
#: stopped raising reddens too, so this cannot rot into a silent exemption.
#: The planted value still reaches the report in this case - saferepr replaces
#: only the RECEIVER's rendering - so the arm still measures what it is for.
REPR_RAISING_HOLDERS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "tests/save/test_properties.py": (
            "_HostileRepr is a test double whose repr calls the field the arm "
            "plants into, so the planted value is invoked and raises"
        )
    }
)

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

#: The three classes the acceptance names, in the order it names them, each
#: with the per-arm suffix that makes one arm's planted value distinguishable
#: from another's. Every suffix is FIXED WIDTH so no arm's token is a substring
#: of another arm's, which is what lets a grep answer for exactly one arm.
SENSITIVE_TOKEN_FORMS: Final = (
    (SAVE_NAME_TOKEN, "Arm{index:02d}"),
    (HOME_PATH_TOKEN, "/arm{index:02d}"),
    (ACCOUNT_DIR_TOKEN, "{index:02d}"),
)

#: The three classes the acceptance names, in the order it names them.
SENSITIVE_TOKENS: Final = tuple(base for base, _ in SENSITIVE_TOKEN_FORMS)

#: The suffix a repo-relative module path carries. Named rather than spelled
#: inline because the guard module is forbidden one and this is the only place
#: the conversion happens.
PY_SUFFIX: Final = ".py"

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
#: IT WAS EMPTY, AND THE TWO ENTRIES BELOW ARE WHAT WIDENING THE BINDING RULE
#: REVEALED. The previous sole entry named tests/save/test_struct_interior.py,
#: whose confinement arm was repaired by the CS-829 merge; the both-directions
#: assertion went RED on that merge and is what required it to be deleted
#: rather than left to rot. The same assertion will require these two to go the
#: moment their sites are repaired.
#:
#: NEITHER IS ON THE WRITE-LIST OF THE SLICE THAT FOUND THEM, which is the
#: whole reason they are recorded rather than fixed. Editing another slice's
#: file mid-session is how three parallel slices collide, so they are handed on
#: with their shape named. Both are the SAME defect as the one repaired in
#: tests/save/test_world.py: an aggregate built from a withheld field and then
#: rendered by an assertion over it.
LIVE_DISCLOSURE_RESIDUALS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "tests/save/test_usmap.py": (
            "a list comprehension over PropertyMap.warnings is bound and then "
            "rendered by an inline len() in the assertion over it. FLAGGED ON "
            "SHAPE, CLEAN ON CONTENT: this module never loads a real save - "
            "every PropertyMap in it comes from synthetic.build_usmap, and the "
            "module's only mention of load_world is inside a comment. The shape "
            "is a true positive and the remedy is a scalar bound first, but no "
            "save-derived value reaches this frame today. Two agents disagreed "
            "on this entry and the merger measured it; do not restate it as a "
            "live disclosure without re-measuring the module's save reach"
        ),
        "tests/test_hook_interpreter_ladder.py": (
            "a sorted() comprehension whose ITERABLE is Environment.variables "
            "is bound and then asserted on. The derived list holds variable "
            "NAMES rather than values, so this is the conservative direction "
            "of the comprehension rule rather than a measured disclosure. "
            "Outside the finding slice's write-list"
        ),
    }
)


def _functions_reached(source: str, linenos: Sequence[int]) -> set[str]:
    """Which functions of a synthetic source at least one finding landed inside.

    Args:
        source: The synthetic module.
        linenos: The lines the detector reported.

    Returns:
        The names of the enclosing functions. This is what turns a count of
        sites into a per-shape verdict, so one shape contributing two findings
        cannot pay for another contributing none.
    """
    reached: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        last = node.end_lineno or node.lineno
        if any(node.lineno <= number <= last for number in linenos):
            reached.add(node.name)
    return reached


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


CARRIER_BINDING_SOURCE: Final = '''
"""A withheld field routed into a local through a wrapper that CARRIES it.

Every function here binds the field into a name and then asserts on that name.
The binding is what the guard has to follow: the assertion itself renders only
a local, so a scan that stops at the assert sees nothing in any of them.
"""


class Holder:
    words: frozenset[str]
    count: int

    def __repr__(self) -> str:
        return f"Holder(words={len(self.words)}, count={self.count})"


def in_a_list(holder: Holder) -> None:
    box = [holder.words]
    assert len(box) == 0


def in_a_tuple(holder: Holder) -> None:
    box = (holder.words,)
    assert len(box) == 0


def in_a_set(holder: Holder) -> None:
    box = {holder.words}
    assert len(box) == 0


def in_a_dict(holder: Holder) -> None:
    box = {"k": holder.words}
    assert len(box) == 0


def in_a_comprehension(holder: Holder) -> None:
    box = [word for word in holder.words]
    assert len(box) == 0


def in_an_fstring(holder: Holder) -> None:
    box = f"{holder.words}"
    assert len(box) == 0


def in_a_branch(holder: Holder) -> None:
    box = holder.words if holder.count else frozenset()
    assert len(box) == 0


def through_a_transparent_call(holder: Holder) -> None:
    box = sorted(holder.words)
    assert len(box) == 0


def through_an_element_reducer(holder: Holder) -> None:
    box = max(holder.words)
    assert box == ""


def through_two_hops(holder: Holder) -> None:
    box = [holder.words]
    kept = [value for value in box if value]
    assert len(kept) == 0
'''


def _asserting_functions(source: str) -> set[str]:
    """Every function in a synthetic source that carries an ``assert``.

    DERIVED FROM THE FIXTURE'S OWN DECLARATIONS rather than from what the
    detector reported, so adding a shape to the source above makes the test
    demand coverage of it instead of quietly widening the population it passes
    over. A fixture shape with no assertion is not a site and is skipped.

    Args:
        source: The synthetic module.

    Returns:
        The function names.
    """
    return {
        node.name
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ANY_FUNCTION)
        and any(isinstance(inner, ast.Assert) for inner in ast.walk(node))
    }


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


def test_a_binding_that_carries_a_withheld_field_is_flagged():
    # THE COMPLETENESS REFUTATION THAT REOPENED CS-850, and it was found by an
    # adversary assigned to a different question. The scan read what a binding
    # CARRIED with the same one-level test it uses on an asserted node, so a
    # withheld field wrapped in ANYTHING - a list literal, a comprehension, an
    # f-string, a branch, a transparent call - lost its alias at the binding and
    # every later assertion over that local walked free. Ten shapes measured on
    # the pre-repair guard, ZERO flagged.
    #
    # Graded PER SHAPE rather than by a total, because a pooled count is met by
    # whichever shape contributes most while the rest go unmeasured. The
    # expected set is read out of the fixture's own AST, so a shape added below
    # is demanded rather than absorbed.
    found = scan_source("<carrier>", CARRIER_BINDING_SOURCE)
    reached = _functions_reached(CARRIER_BINDING_SOURCE, [finding.lineno for finding in found])
    missed = sorted(_asserting_functions(CARRIER_BINDING_SOURCE) - reached)
    unswept = len(missed)
    assert unswept == 0, (
        f"{unswept} binding shapes hand a withheld field to a local and are not "
        f"flagged when that local is asserted on: {missed}. pytest reprs the "
        "sub-expression it finds, and a wrapper is not a mask unless it cannot "
        "carry its argument's contents through"
    )


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


class _Arm(NamedTuple):
    """One forced arm: which shipped class it builds and what it plants in it.

    Deliberately WITHOUT a hand-written ``__repr__``, so this class does not
    join the population it is used to grade and add an eleventh arm that
    imports this module into its own sandbox. Every field it holds is either a
    repo path or a synthetic token.

    Attributes:
        position: Place in the derived order, which fixes the token class.
        module: Repo-relative path of the module the arm represents.
        holder: The redacting class shipped by that module.
        field: The withheld field the arm renders.
        fields: Every field of that class, needed to build an instance.
        token: The synthetic sensitive value planted in ``field``, unique to
            this arm so one arm's leak cannot stand in for another's.
        marker: A synthetic tag carried in the arm's counts-only message, so
            "this arm reached its assertion" is measurable per arm.
    """

    position: int
    module: str
    holder: str
    field: str
    fields: tuple[str, ...]
    token: str
    marker: str


def _dotted(module: str) -> str:
    """The import name of a repo-relative module path.

    Args:
        module: A path such as the one a finding carries.

    Returns:
        The dotted name.
    """
    return module.removesuffix(PY_SUFFIX).replace("/", ".")


def _receiver_rendering(output: str, arm: _Arm) -> str | None:
    """How the arm's holder rendered in the explanation chain that leaked.

    Args:
        output: The sandbox's combined output.
        arm: The arm.

    Returns:
        The text pytest printed for the object the withheld field was read
        from, or None when no such chain was rendered. Read out of the line
        that carries this arm's own unique token, so one arm's chain can never
        answer for another's.
    """
    tail = f".{arm.field}"
    for line in output.splitlines():
        if arm.token in line and line.endswith(tail) and RENDERED_EQUALS in line:
            return line.split(RENDERED_EQUALS, 1)[1][: -len(tail)]
    return None


def _fired(output: str, arm: _Arm) -> bool:
    """Whether one arm reached its own assertion and failed there.

    Read from the raised message rather than from the short summary, which
    pytest truncates to the terminal width - measured at 80 characters for
    these arms, which is exactly on the edge.

    Args:
        output: The sandbox's combined output.
        arm: The arm.

    Returns:
        True when the arm's own counts-only message was raised with a count of
        one, which is the number of entries planted in its field.
    """
    return f"AssertionError: 1 - counts only {arm.marker}" in output


def _covered_modules() -> list[tuple[str, str, str, tuple[str, ...]]]:
    """One (module, class, withheld field, all fields) per module this covers.

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
        that ships one, plus that class's whole field list, sorted so the
        arm-to-token assignment is deterministic.
    """
    declarations, _ = scan_repo()
    chosen: dict[str, tuple[str, str, tuple[str, ...]]] = {}
    for entry in sorted(declarations, key=lambda entry: (entry.module, entry.lineno)):
        if entry.withheld:
            chosen.setdefault(
                entry.module,
                (entry.name, sorted(entry.withheld)[0], tuple(entry.fields)),
            )
    return [
        (module, holder, field, fields)
        for module, (holder, field, fields) in sorted(chosen.items())
    ]


def _representative_arms() -> list[_Arm]:
    """One forced arm per COVERED module, with a sensitive token planted in it.

    THE TOKEN IS UNIQUE PER ARM, and that is not decoration. The previous
    spelling gave ten arms three shared tokens and then asserted the SET of
    tokens was rendered, so one arm leaking its class's token satisfied the
    assertion for every other arm carrying the same one - a pooled threshold
    met by its strongest member while its weakest went unmeasured. The suffixes
    are fixed width within a class, so no arm's token is a substring of
    another's and a grep for one cannot answer for two.

    Returns:
        One arm per covered module. The token class cycles through the three
        the acceptance names so every one is exercised.
    """
    arms: list[_Arm] = []
    for index, (module, holder, field, fields) in enumerate(_covered_modules()):
        base, suffix = SENSITIVE_TOKEN_FORMS[index % len(SENSITIVE_TOKEN_FORMS)]
        arms.append(
            _Arm(
                position=index,
                module=module,
                holder=holder,
                field=field,
                fields=fields,
                token=base + suffix.format(index=index),
                marker=f"cs850arm{index:02d}",
            )
        )
    return arms


def test_the_forced_arms_survive_every_leak_being_repaired():
    # THE PROOF MUST NOT BE ANTI-MONOTONE IN THE PROPERTY IT CERTIFIES.
    # Measured on the previous spelling: live=3 green, live=2 red, live=1 red,
    # live=0 red. Repairing a leak broke the proof that leaks are repaired, and
    # a sibling slice hardening seven sites that were never leaks would have
    # done it at the merge rather than hypothetically.
    _, findings = scan_repo()
    leaking = {finding.module for finding in findings if finding.live}
    covered = {arm.module for arm in _representative_arms()}
    survivors = sorted(covered - leaking)
    remaining = len(survivors)
    assert remaining >= len(SENSITIVE_TOKENS), (
        f"only {remaining} of {len(covered)} forced arms sit in a module with "
        f"no live finding, and {len(SENSITIVE_TOKENS)} are needed to plant one "
        "of each sensitive class. Repairing the remaining leaks would turn this "
        "module's own acceptance red"
    )


#: What each sandbox does with the aggregate before asserting on it.
ARM_LEAKING: Final = "leaking"
ARM_REMEDIED: Final = "remedied"
ARM_FLOOR: Final = "floor"

#: The sandbox's own scaffolding, written once above the arms.
#:
#: ``_build`` IS WHAT MAKES AN ARM AN ARM OF ITS MODULE. It imports the module
#: the arm represents, resolves the redacting class BY NAME out of it, and
#: builds an instance whose withheld field holds the planted value. Everything
#: rendered below the assertion is then the SHIPPED class's own ``__repr__``
#: and the SHIPPED field, not a generated look-alike.
#:
#: TWO CONSTRUCTION PATHS, because the population needs both and neither
#: reaches the other's classes - MEASURED, not assumed. A ``NamedTuple`` stores
#: its fields in the tuple itself and ``object.__new__`` on one raises
#: ``TypeError``, so ``_make`` is the only way in; a frozen dataclass raises
#: ``FrozenInstanceError`` from its own ``__setattr__``, so it needs
#: ``object.__new__`` plus ``object.__setattr__``. Both bypass ``__init__``
#: deliberately: a constructor's argument types are the shipped module's
#: business and are not what this measures.
#:
#: ``_Filler`` IS A STAND-IN FOR THE FIELDS THE ARM IS NOT ABOUT, and it has to
#: answer whatever a shipped ``__repr__`` asks. The reprs in this tree call
#: ``len``, ``sum(... .values())``, ``is not None``, ``!r`` and a project
#: digest helper on their own fields, so the filler is a ``str`` that also
#: answers the mapping protocol and a call. It holds the empty string, so
#: nothing it renders can carry anything.
SANDBOX_PRELUDE: Final = '''"""Generated by the CS-850 forced arms - synthetic tokens only."""

import importlib


class _Filler(str):
    """A benign stand-in answering whatever a shipped __repr__ asks of a field."""

    def items(self):
        return ()

    def keys(self):
        return ()

    def values(self):
        return ()

    def __call__(self, *args, **kwargs):
        return None


def _build(dotted, class_name, fields, field, planted):
    holder = getattr(importlib.import_module(dotted), class_name)
    values = {name: _Filler("") for name in fields}
    values[field] = planted
    order = getattr(holder, "_fields", None)
    if order is not None:
        return holder._make([values.get(name, _Filler("")) for name in order])
    item = object.__new__(holder)
    for name, value in values.items():
        object.__setattr__(item, name, value)
    return item
'''


def _arm_source(arm: _Arm, *, form: str) -> str:
    """The text of one forced arm, in whichever of the three forms is wanted.

    THE TOKEN IS BOUND AT MODULE SCOPE AND NAMED IN THE BODY, never spelled
    inside the failing function. MEASURED: the first spelling planted it as a
    literal in the test body, and the REMEDIED arm leaked all three tokens
    anyway - pytest renders the failing function's own SOURCE LINES above the
    assertion, so the literal was printed by the traceback rather than by the
    rewriter. That is a second channel with a second remedy, and grading it as
    if it were this one would have reported the fix as failing when it worked.
    Re-measured while this generator was rewritten: a module-scope binding
    renders ZERO times, the failing function's docstring and its comments
    render once each, and a line below the failing one renders zero times.

    THE PLANTED VALUE IS A ONE-ENTRY MAPPING, so ``len`` of it is 1 in every
    arm. That fixed number is what lets the arm's own counts-only message carry
    a per-arm marker AND a known count, which is how "this arm reached its
    assertion" becomes measurable per arm rather than pooled.

    Args:
        arm: The arm to write.
        form: :data:`ARM_LEAKING`, :data:`ARM_REMEDIED` or :data:`ARM_FLOOR`.

    Returns:
        Python source for one planted value and one test.
    """
    planted = f"PLANTED_{arm.position:02d}"
    read = f"item.{arm.field}"
    message = f'f"{{count}} - counts only {arm.marker}"'
    if form == ARM_LEAKING:
        body = f'    assert len({read}) <= 0, f"{{len({read})}} - counts only {arm.marker}"\n'
    else:
        comparison = ">= 0" if form == ARM_FLOOR else "<= 0"
        body = f"    count = len({read})\n    assert count {comparison}, {message}\n"
    return (
        f"{planted} = {{{arm.token!r}: 1}}\n"
        f"\n"
        f"def test_forced_arm_{arm.position:02d}():\n"
        f"    item = _build({_dotted(arm.module)!r}, {arm.holder!r}, "
        f"{arm.fields!r}, {arm.field!r}, {planted})\n"
        f"{body}"
    )


def _sandbox_module(*, form: str) -> str:
    """A whole sandbox module: one forced arm per guarded module.

    Args:
        form: Which form of the arms to write.

    Returns:
        Python source.
    """
    parts = [SANDBOX_PRELUDE]
    parts += [_arm_source(arm, form=form) for arm in _representative_arms()]
    return "\n\n".join(parts)


def _run_sandbox(root: Path, *, form: str) -> tuple[int, str]:
    """Write the sandbox and run real pytest over it.

    The sandbox has no conftest, no rootdir in this repository and no cache,
    because the subject is what pytest itself prints and a redactor running
    over the top would grade the redactor instead. What it DOES get is this
    repository on ``PYTHONPATH``, which is how each arm reaches the shipped
    class it represents.

    THE CAPTURED TEXT IS REDACTED BEFORE IT LEAVES THIS FUNCTION, and that is
    not decoration. pytest renders a fixture's value in the failure header of
    every test that names it, and the sandbox's own header line carries its
    rootdir - a temporary directory that on this platform sits under the
    operator's profile and embeds their account name. The planted tokens are
    synthetic and survive the redaction, which is not assumed:
    ``test_the_unremedied_arms_render_every_planted_token`` measures every one
    of them still present in the text this returns.

    Args:
        root: A directory to write into.
        form: Which form of the arms to write.

    Returns:
        pytest's own exit code, and its combined output with this machine's
        spellings removed.
    """
    root.mkdir(parents=True, exist_ok=True)
    target = root / "test_forced_arms.py"
    target.write_bytes(_sandbox_module(form=form).encode("ascii"))
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(REPO_ROOT)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
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
        env=environment,
        timeout=SUBPROCESS_TIMEOUT,
    )
    text = (completed.stdout + completed.stderr).decode("utf-8", errors="replace")
    return (completed.returncode, redact_personal_data(text))


@pytest.fixture(scope="module")
def leaking_arms(tmp_path_factory: pytest.TempPathFactory) -> tuple[int, str]:
    """The forced arms in the shape the tree ships - the CONTROL."""
    return _run_sandbox(tmp_path_factory.mktemp("cs850_leaking"), form=ARM_LEAKING)


@pytest.fixture(scope="module")
def remedied_arms(tmp_path_factory: pytest.TempPathFactory) -> tuple[int, str]:
    """The same arms with the aggregate bound to a scalar first."""
    return _run_sandbox(tmp_path_factory.mktemp("cs850_remedied"), form=ARM_REMEDIED)


@pytest.fixture(scope="module")
def floor_arms(tmp_path_factory: pytest.TempPathFactory) -> tuple[int, str]:
    """The same arms with the comparison unforced - the PRISTINE FLOOR."""
    return _run_sandbox(tmp_path_factory.mktemp("cs850_floor"), form=ARM_FLOOR)


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
    planted = {arm.token for arm in _representative_arms()}
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
    # AND EACH ARM MUST HAVE REACHED ITS OWN ASSERTION. An arm that raised
    # inside _build fails too, exits 1 too, and renders no planted token
    # either - so without this the clean grep below is satisfied by ten arms
    # that never built a shipped object at all.
    silent = sorted(arm.marker for arm in _representative_arms() if not _fired(output, arm))
    unreached = len(silent)
    assert unreached == 0, (
        f"{unreached} remedied arms never reached their assertion, so the "
        f"clean grep below is about arms that did not run: {silent}"
    )
    planted = {arm.token for arm in _representative_arms()}
    leaked = sorted(token for token in planted if token in output)
    survivors = len(leaked)
    assert survivors == 0, (
        f"{len(leaked)} planted tokens survived the remedy into the rendered "
        "failure report. Binding the aggregate to a scalar is the whole fix, so "
        "a token still present means the rendered expression still holds the "
        "container: " + repr(leaked)
    )


def test_every_forced_arm_reached_its_assertion_through_shipped_construction(
    leaking_arms: tuple[int, str],
):
    # THE ARMS MUST EXECUTE SHIPPED CODE, and this is what measures that they
    # did. Each arm reaches its assertion only by importing the module it
    # represents, resolving the redacting class BY NAME out of it, and building
    # an instance - so a missing module, a renamed class or a field that is no
    # longer there raises before the assert and the marker below never appears.
    # A generated stand-in with no imports proves a property of pytest's
    # rewriter; this proves the shipped class is what was rendered.
    #
    # PER ARM AND NOT POOLED. A threshold summed over the arms is met by its
    # strongest member while its weakest goes unmeasured.
    _, output = leaking_arms
    arms = _representative_arms()
    silent = sorted(arm.marker for arm in arms if _fired(output, arm) is False)
    unreached = len(silent)
    assert unreached == 0, (
        f"{unreached} of {len(arms)} forced arms never reached their own "
        "assertion, so whatever the grep below reads, it is not those arms "
        f"failing on a shipped class: {silent}"
    )


def test_the_forced_arms_are_green_before_they_are_forced(floor_arms: tuple[int, str]):
    # THE PRISTINE FLOOR. The same arms, built the same way out of the same
    # shipped classes, with the comparison left unforced. Without it a red
    # sandbox is ambiguous between "the forcing worked" and "_build is broken
    # and every arm errors", and those two produce the same exit code.
    code, output = floor_arms
    arms = _representative_arms()
    collected = f"collected {len(arms)} item" in output
    assert collected, f"the floor sandbox did not collect all {len(arms)} arms"
    assert code == PYTEST_ALL_PASSED, (
        f"the floor sandbox exited {code}; expected {PYTEST_ALL_PASSED}. The "
        "arms are not green before they are forced, so a red forced run does "
        "not measure the forcing"
    )
    leaked = sorted(arm.marker for arm in arms if arm.token in output)
    survivors = len(leaked)
    assert survivors == 0, (
        f"{survivors} planted tokens were rendered by arms that PASSED, so "
        f"something other than a failure report is printing them: {leaked}"
    )


def test_the_shipped_repr_is_what_gets_bypassed_in_every_forced_arm(
    leaking_arms: tuple[int, str],
):
    # WHOSE __repr__ RAN IS THE HALF THAT MAKES THESE ARMS ABOUT SHIPPED CODE.
    # The rendered explanation chain reads `<receiver> = <repr>.<field>`, and
    # that repr is the shipped class's own. A generated look-alike could print
    # the same shape while proving nothing about the module it was named after.
    _, output = leaking_arms
    arms = _representative_arms()
    unresolved = sorted(arm.marker for arm in arms if _receiver_rendering(output, arm) is None)
    unread = len(unresolved)
    assert unread == 0, (
        f"{unread} arms rendered no `<repr>.<field>` chain at all, so what "
        f"reached the report is not a read of the shipped field: {unresolved}"
    )
    # A repr that RAISES renders a saferepr apology instead, and one shipped
    # class does that on purpose. Recorded in both directions, so a second one
    # appearing reddens and this one being repaired reddens too.
    raising = {
        arm.module for arm in arms if REPR_RAISED_MARKER in (_receiver_rendering(output, arm) or "")
    }
    unexpected = sorted(raising - set(REPR_RAISING_HOLDERS))
    assert not unexpected, (
        "a shipped __repr__ raised while rendering a forced arm and nothing "
        f"records why: {unexpected}. Either the class stopped withholding "
        "safely or the arm is planting a value it cannot hold"
    )
    repaired = sorted(set(REPR_RAISING_HOLDERS) - raising)
    assert not repaired, f"these reprs no longer raise; delete their entries: {repaired}"


def test_every_sensitive_class_is_covered_by_the_forced_arms():
    # The acceptance names three classes. A proof that plants only one of them
    # and reports a pass is a proof about one class wearing the name of three.
    planted = {arm.token for arm in _representative_arms()}
    uncovered = sorted(
        base for base in SENSITIVE_TOKENS if not any(one.startswith(base) for one in planted)
    )
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
    # PER SHAPE AND NOT POOLED. The previous spelling compared a COUNT of
    # rendered sites against a threshold, and a count summed over the shapes is
    # met by its strongest member: one shape contributing an extra site paid
    # for another shape contributing none, and the one that had gone silent was
    # never named. Each shape is now asked for itself.
    found = scan_source("<evasion>", EVASION_SOURCE)
    reached = _functions_reached(EVASION_SOURCE, [finding.lineno for finding in found])
    missed = sorted(name for name in EVASION_FUNCTIONS if name not in reached)
    silent = len(missed)
    assert silent == 0, (
        f"{silent} of the {len(EVASION_FUNCTIONS)} evasion shapes render the "
        "withheld frozenset and the detector reached none of their sites. Each "
        "one below is a different way of binding the same field:\n"
        + "\n".join(f"  {name}" for name in missed)
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


def test_the_reducer_vocabulary_is_partitioned_by_what_survives():
    # CS-497's LESSON APPLIED TO THE REDUCERS. The two halves below decide
    # whether a BINDING through a reducer keeps its alias, and the cheap
    # spelling - deriving one half by subtracting the other - makes a name
    # classified nowhere land on the withholding side by arithmetic. That is the
    # direction that hides a leak, and it is silent. Both halves are read here,
    # so forgetting one costs a red that names it.
    unclassified = sorted(CONTENT_REDUCERS - (ELEMENT_REDUCERS | MEASURE_REDUCERS))
    invented = sorted((ELEMENT_REDUCERS | MEASURE_REDUCERS) - CONTENT_REDUCERS)
    both_sides = sorted(ELEMENT_REDUCERS & MEASURE_REDUCERS)
    faults = len(unclassified) + len(invented) + len(both_sides)
    assert faults == 0, (
        f"the reducer partition is broken: {unclassified} are classified "
        f"nowhere, {invented} are classified but are not reducers, and "
        f"{both_sides} are on both sides. A reducer classified nowhere is read "
        "as withholding, which is the direction that loses a leak in silence"
    )


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
    # NO EVIDENCE IS A SKIP RATHER THAN A RED, and requiring the difference was
    # the same defect this module records twice elsewhere: a proof whose passing
    # condition is that today's tree still contains the thing it looks for.
    # MEASURED: the margin is a SINGLE field, from a single class - WorldModel's
    # `token`, masked by `masked_token` imported from clockspeed/save/header.py.
    # Inlining that helper into world.py - identical body, no leak, no privacy
    # change at all - takes the two totals level and turns this RED. A
    # legitimate refactor must not redden a privacy suite.
    #
    # THE CAPABILITY IS NOT LOST BY SKIPPING, and that is what makes the skip
    # safe rather than a hole: `gained` is computed from DECLARATIONS and never
    # from findings, so a green run here only ever certified that a cross-module
    # mask EXISTS somewhere - not that a leak does. The synthetic twin
    # `test_the_cross_module_mask_hop_is_proven_without_the_tree` forces the hop
    # against sources it authors itself and survives the refactor, so it is the
    # arm that proves the resolver works. This one adds only that the tree
    # currently exercises it, and a tree that stops has nothing to report.
    #
    # The assertion that remains is NOT vacuous: resolving tree-wide can never
    # withhold FEWER fields than resolving module by module, so a negative
    # margin is an inversion in the resolver and still reddens.
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
    if gained == 0:
        pytest.skip(
            "no class in the tree masks a field through a function imported "
            "from another module, so this arm has no subject on it today. The "
            "resolver itself is proven by the synthetic twin"
        )
    assert gained > 0, (
        f"resolving masks tree-wide withheld {tree_wide} fields and resolving "
        f"module by module withheld {local_only}. Tree-wide resolution "
        "recognises strictly more masks, so it can never withhold fewer - a "
        "negative margin means the resolver has inverted"
    )


IMPORTED_MASK_OWNER_SOURCE: Final = """
\"\"\"The module that DEFINES a project mask.\"\"\"


def masked(token):
    digest = sha256(token).hexdigest()
    return digest[:8]
"""

IMPORTED_MASK_USER_SOURCE: Final = """
\"\"\"The module that IMPORTS it and reprs through it.\"\"\"


class Model:
    token: str

    def __repr__(self) -> str:
        return f"Model(token={masked(self.token)!r})"
"""


def test_the_cross_module_mask_hop_is_proven_without_the_tree():
    # THE SAME CAPABILITY AS THE TEST ABOVE, PROVEN ON SYNTHETIC SOURCE. That
    # one measures a DIFFERENCE on the real tree, so it needs the tree to
    # contain at least one mask defined in one module and imported by another -
    # true today, and a property a refactor could remove without any leak
    # existing. This proves the hop itself on two hand-authored modules, whose
    # verdicts cannot change when the tree does.
    owner = ast.parse(IMPORTED_MASK_OWNER_SOURCE)
    user = ast.parse(IMPORTED_MASK_USER_SOURCE)
    opaque = frozenset({"Model"})
    local_only = guard.redacting_classes("<user>", user, opaque)
    tree_wide = guard.redacting_classes("<user>", user, opaque, guard.module_functions(owner))
    graded_alone = sorted(name for entry in local_only for name in entry.withheld)
    graded_together = sorted(name for entry in tree_wide for name in entry.withheld)
    assert graded_alone == [], (
        "a mask this module cannot see was already read as withholding, so the "
        f"probe cannot show the hop buying anything. It graded {graded_alone}"
    )
    assert graded_together == ["token"], (
        "resolving the IMPORTED mask did not put the field back under the "
        f"guard. It graded {graded_together}, so a leak over a field masked by "
        "an imported helper would pass the sweep in silence"
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


def _account_position_probe(planted: str) -> str:
    """One synthetic function whose docstring sits a segment below the save root.

    The save-root marker is DERIVED from the resolver's own parts rather than
    spelled here, so a relocation moves the probe with the rule it exercises.

    Args:
        planted: The synthetic account-directory token to sit below the root.

    Returns:
        Python source for one failing function.
    """
    marker = "/".join(SAVE_ROOT_PARTS)
    return f'def render():\n    """{marker}/{planted}"""\n    assert 1 == 0\n'


def test_the_source_echo_detector_reads_this_machine_out_of_a_planted_docstring():
    # THE MACHINE RULE, AND IT IS THE ONE THAT CANNOT FALSE-POSITIVE. It asks
    # whether the project's own runtime redactor recognises something in the
    # rendered source, so it fires on a REAL spelling and on nothing else. The
    # spelling is read off this machine at run time and never written down;
    # what is reported below is a count and a verdict.
    #
    # PLANTED IN A COMMENT, which needs no escaping for a Windows path and is
    # MEASURED to be inside the channel: a comment above the failing line
    # rendered once in a real failure report, and a line below it rendered zero
    # times - which is why the sweep reads the whole function rather than
    # trying to guess which line fails.
    planted = f"def render():\n    # {Path.home()}\n    assert 1 == 0\n"
    echoes = source_echoes("<machine>", planted)
    kinds = sorted({echo.kind for echo in echoes})
    assert ECHO_MACHINE in kinds, (
        "the machine rule did not fire on this machine's own home spelling "
        f"planted in a rendered docstring. It reported {kinds}, so the sweep "
        "below is looking for nothing"
    )


def test_the_source_echo_detector_flags_a_planted_home_path_and_account_directory():
    # THE TWO SHAPE RULES, each borrowed from the module that owns it rather
    # than respelled here. Both tokens are synthetic and safe to plant.
    home = f'def render():\n    """{HOME_PATH_TOKEN}"""\n    assert 1 == 0\n'
    account = _account_position_probe(ACCOUNT_DIR_TOKEN)
    home_kinds = sorted({echo.kind for echo in source_echoes("<home>", home)})
    account_kinds = sorted({echo.kind for echo in source_echoes("<account>", account)})
    assert ECHO_HOME in home_kinds, f"the home-path rule reported {home_kinds}"
    assert ECHO_ACCOUNT in account_kinds, f"the account rule reported {account_kinds}"


def test_the_source_echo_detector_reads_only_what_pytest_renders():
    # MEASURED UNDER REAL PYTEST, not reasoned about: a token bound at MODULE
    # scope rendered ZERO times in a failure report while the same token in the
    # failing function's DOCSTRING rendered once. So the docstring is inside
    # this rule's subject and the module-scope binding is outside it, and
    # reading them alike would report a shape pytest never prints.
    outside = f'PLANTED = "{HOME_PATH_TOKEN}"\n\n\ndef render():\n    assert 1 == 0\n'
    echoes = source_echoes("<outside>", outside)
    flagged = len(echoes)
    assert flagged == 0, (
        f"the detector reported {flagged} echoes for a token bound at module "
        "scope, which pytest does not render into a failure report"
    )


def test_the_source_echo_detector_reads_a_decorator_line():
    # MEASURED UNDER REAL PYTEST, AND IT REFUTES WHAT THIS SWEEP USED TO CLAIM.
    # The docstring here said "pytest starts its rendering at the def", so the
    # floor was FunctionDef.lineno and every decorator line sat below it. A
    # planted literal inside @pytest.mark.skipif(...) - not a parametrize value,
    # not an argument - was printed VERBATIM above the def under completely
    # default flags, once per decorated failure, in a report where the sweep
    # reported nothing.
    #
    # A decorator can also hold a fixture name, a path or a marker reason, so
    # this is a real surface rather than a technicality.
    planted = (
        "import pytest\n\n\n"
        f'@pytest.mark.skipif(False, reason="{HOME_PATH_TOKEN}")\n'
        "def render():\n"
        "    assert 1 == 0\n"
    )
    kinds = sorted({echo.kind for echo in source_echoes("<decorator>", planted)})
    assert ECHO_HOME in kinds, (
        f"the sweep reported {kinds} for a home path planted in a DECORATOR. "
        "pytest prints decorator source lines above the def, so a floor set at "
        "the def leaves every one of them unswept"
    )


def test_no_shipped_function_echoes_personal_data_through_its_own_source():
    # THE SWEEP for the second channel. pytest prints the failing function's
    # own source lines above the assertion, so a sensitive value written
    # LITERALLY into a function body reaches the failure report without the
    # rewriter touching it. There is no allowlist here on purpose: an authored
    # home path or account directory has one disposition, which is deletion.
    scanned, echoes = scan_repo_source_echoes()
    assert scanned > 1, (
        f"the source-echo sweep read {scanned} functions. At one or fewer it is "
        "reading a file rather than the repository"
    )
    reddening = len(echoes)
    assert reddening == 0, (
        "a function's own source carries a value that pytest renders above the "
        "assertion when it fails, with no rewriter involved (CLAUDE.md "
        "non-negotiables 11 and 12). Auto-detect it at run time instead:\n"
        + describe_echoes(echoes)
    )


def test_the_source_echo_boundary_is_pinned_rather_than_silently_absent():
    # THE BOUNDARY, MEASURED. The rule above reaches two of the three classes
    # the acceptance names. A SAVE-DERIVED NAME has no shape - a world name is
    # operator-authored free text, derivable from nothing on this machine - so
    # no static rule can recognise one, which is the same asymmetry
    # test_the_runtime_redactor_cannot_reach_a_save_derived_name measures for
    # the runtime net. And the account-id DIGIT-RUN backstop is not applied to
    # authored source: measured over every rendered source line in the tree it
    # reported 15 matches on 12 distinct lines, and every one was a decimal
    # fraction in prose, a byte count, an int64 fixture value or a deliberately
    # fake credential rather than an account directory. The positional rule
    # that locate.py calls its PRIMARY one is used instead.
    name_only = f'def render():\n    """{SAVE_NAME_TOKEN}"""\n    assert 1 == 0\n'
    bare_digits = f'def render():\n    """{ACCOUNT_DIR_TOKEN}"""\n    assert 1 == 0\n'
    uncovered = {
        "a save-derived name with no shape": len(source_echoes("<name>", name_only)),
        "an account-shaped digit run outside a save path": len(
            source_echoes("<digits>", bare_digits)
        ),
    }
    covered = sorted(label for label, found in uncovered.items() if found)
    assert covered == [], (
        "the pinned boundary has moved. Shapes now COVERED that this record "
        f"still calls uncovered: {covered}. Update the record - a boundary "
        "statement that is no longer true is worse than none"
    )


def test_every_source_echo_rule_is_borrowed_rather_than_respelled():
    # ONE VOCABULARY, ONE READER, on the same terms as the locator seeds and
    # the declaration reader. Each rule below is owned by another module and
    # imported here; a second spelling would be CS-433's defect again. A
    # borrowed reader that fails to load makes the sweep go SILENT rather than
    # loud, so its reachability is asserted rather than assumed.
    missing = sorted(
        label
        for label, reader in (
            (ECHO_MACHINE, guard._borrowed_machine_redactor()),  # noqa: SLF001
            (ECHO_HOME, guard._borrowed_home_path_reader()),  # noqa: SLF001
            (ECHO_ACCOUNT, guard._borrowed_account_position_rule()),  # noqa: SLF001
        )
        if reader is None
    )
    unreachable = len(missing)
    assert unreachable == 0, (
        f"{unreachable} of the source-echo rules could not load their owning "
        f"module, so the sweep is not applying them at all: {missing}"
    )


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


# ---------------------------------------------------------------------------
# CS-1199 - no assertion renders a process-environment VALUE
# ---------------------------------------------------------------------------
#
#
# THE DEFECT. ``tests/test_doc_budget.py`` carried::
#
#     before = dict(os.environ)
#     doc_budget.evaluate(REPO_ROOT)
#     assert dict(os.environ) == before
#
# pytest rewrites that assertion and, on failure, reprs BOTH operands and the
# ``os.environ`` argument inside the call - every environment value, live API
# credentials included, into the local log and into CI output. The message of an
# assertion does not control that channel; ``tests/assertion_rendering_guard.py``
# names the mechanism in full.
#
# WHY THE CS-850 GUARD DID NOT SEE IT, stated as that guard's own boundary rather
# than as a bug in it. ``tests/assertion_rendering_guard.py`` grades ONE class of
# defect: an assertion rendering a field that a class DECLARED unsafe by shipping
# a hand-written, withholding ``__repr__``. ``os.environ`` is an ``os._Environ``
# whose repr discloses everything, and ``dict(os.environ)`` is a plain dict - there
# is no declaration to bypass, so both are outside that guard by construction, as
# its docstring says ("a plain dict, list or set"). This module closes the
# environment subset of that gap by SOURCE rather than by declaration: the process
# environment is a named source, and its values are tainted wherever they flow.
#
# MEASURED, NOT ASSUMED - including the shape that looks safe. Run under real
# pytest with a planted token in a controlled child environment,
# ``assert "X" not in os.environ`` renders the whole (truncated) environment,
# because the rewriter's ``visit_Attribute`` reprs ``os.environ`` itself; so do
# ``assert len(os.environ) > 0`` (``visit_Call`` reprs each argument) and
# ``assert os.environ.get("X") is None`` (the value). A membership test is safe
# only once it is bound to a bool BEFORE the assert. The behavioural arm at the
# foot of this module re-measures the flagged shape and the remedy every run.
#
# THE RULE. Every sub-expression pytest's rewriter reprs - :func:`explained` and
# :func:`rendered_parts`, borrowed from the CS-850 guard so the two agree about the
# channel - is graded for whether its VALUE carries an environment value, and so
# is the assertion MESSAGE, which is rendered whole. Environment KEY NAMES are not
# values: ``sorted(os.environ)``, ``set(os.environ)`` and ``os.environ.keys()`` are
# clean, which is what makes the remedy expressible - compare the names of the
# added, removed and changed entries, bound to a list before the assert.
#
# WHERE THE RULE LOOKS. The expression channel exists only in modules pytest
# rewrites - ``test_*.py``, ``*_test.py`` and ``conftest.py`` under ``tests/`` -
# and is graded there. The message channel exists in every assert, rewritten or
# not, and is graded in every tracked ``*.py``.
#
# CALLS ARE RESOLVED ACROSS MODULES, which is the repair of the first refutation.
# The shipped carrier of the environment is ``tests/git_env.py``, imported by
# many modules, and a same-module-only reader read ``scrubbed_env()`` as clean.
# Every module under ``tests/`` that another imports - ``from tests.x import f``,
# ``from .x import f``, ``from tests import x``, ``import tests.x [as m]`` - is
# summarised once (cached, cycle-bounded): per function, what its return carries
# with every parameter clean and with each parameter alone holding the
# environment, so ``scrub(leaky)`` carries and ``plain_git(..., env=env)``,
# whose ``env`` only reaches ``subprocess.run(env=...)``, does not. A top-level
# class that ships a hand-written ``__repr__`` is a SEALED holder: rendering it
# runs that repr, and only its environment-named fields carry.
#
# PARAMETERS ARE GRADED THREE WAYS, which is the repair of the second
# refutation, where ``_run_like_the_hook(layout: HookLayout)`` rendered a
# NamedTuple whose default repr prints its ``env``. A parameter is graded as
# (1) a same-module fixture's provision, (2) what its ANNOTATION names - a class
# with an environment-named field and no hand-written ``__repr__`` is a HOLDER,
# graded as a value, and constructing one is graded the same whatever it was
# handed; a class that seals itself is a sealed holder - and (3) the strongest
# thing any call site in the same module hands it, read on a first pass.
#
# THE UNRESOLVED DEFAULT IS THE CARRYING ONE. A call this module cannot resolve
# and has no vocabulary for is read as carrying every tainted argument into its
# result, with ONE carve-out, measured rather than assumed: a FUNCTION (a
# lower-case callee, or ``subprocess.run`` and its siblings) handed ``env=``
# runs under it and does not return it, while a CONSTRUCTOR handed ``env=``
# holds it. Without that carve-out every ``subprocess.run(..., env=env)`` result
# in the tree read as a leak - over two thousand findings, all false.
#
# STATED LIMITS, named rather than implied away. Each is a DECLARED RESIDUAL.
#   * Production modules under ``clockspeed/``, ``tools/`` and ``scripts/`` are
#     not summarised: they are the subject of the assertions, not a carrier
#     between them. A call into one falls to the unresolved default.
#   * A fixture defined in a ``conftest.py`` is not followed into the test that
#     names it; a same-module fixture is. A call site in ANOTHER module does not
#     seed a parameter, and a call site is recorded only where the guard
#     evaluates it - an assignment, a bare call, a return, an ``if`` or
#     ``while`` test, an assertion.
#   * A holder is recognised by a field NAMED like an environment; a class that
#     keeps one under another name is read as clean.
#   * A lower-case function that RETURNS the ``env=`` it was handed, outside the
#     summarised package, is read as returning clean.
#   * A method of an object that holds the environment - ``repo.commit()`` - is
#     read as returning clean unless it is a string, path or mapping method or is
#     environment-named. The object itself is always graded whole.
#   * An attribute assignment target - ``self.env = dict(os.environ)`` - is not
#     followed. A subscript target taints its container.
#   * A lambda's body, ``getattr`` with a computed attribute name, and a value
#     serialised by any call other than ``json.dumps``, ``pprint.pformat``,
#     ``saferepr``, ``str``, ``repr``, ``ascii`` or ``format`` are not followed.
#   * Taint is STICKY within a scope: a name once bound to an environment value
#     stays tainted even if rebound to something clean. That over-reports; it
#     never under-reports.


#: A value carries no environment content.
ENV_CLEAN: Final = 0
#: An object that HOLDS environment content behind a hand-written ``__repr__``
#: - the ``Environment`` and ``Sandbox`` carriers of CS-703. Rendering it runs
#: that repr, which is what it was written for; the CS-850 guard grades any
#: assertion that bypasses it. Its environment-named FIELDS still carry values.
ENV_SEALED: Final = 1
#: A MAPPING of the environment: rendering it prints values, iterating it
#: yields key NAMES only.
ENV_MAPPING: Final = 2
#: An environment VALUE, or a collection that renders or iterates values. The
#: conservative top: anything that cannot be classified more narrowly is this.
ENV_VALUE: Final = 3

#: Attribute names that ARE the process environment, whatever module alias
#: carries them - ``os.environ``, ``_os.environ``, ``os.environb``.
ENVIRON_ATTRIBUTES: Final = frozenset({"environ", "environb"})

#: Calls that return an environment value whatever their argument.
ENVIRONMENT_READERS: Final = frozenset({"getenv", "getenvb"})

#: Callees that ITERATE their argument. Over a mapping that yields key names -
#: clean - and over values it yields values.
ENV_ITERATING: Final = frozenset(
    {
        "enumerate",
        "filter",
        "frozenset",
        "iter",
        "join",
        "list",
        "map",
        "max",
        "min",
        "next",
        "reversed",
        "set",
        "sorted",
        "tuple",
        "zip",
    }
)

#: Callees that carry their argument's contents through whole, mapping stays
#: mapping.
ENV_PRESERVING: Final = frozenset(
    {"ChainMap", "MappingProxyType", "OrderedDict", "copy", "deepcopy", "dict"}
)

#: Callees that print their argument into a string.
ENV_STRINGIFYING: Final = frozenset(
    {"ascii", "dumps", "format", "pformat", "repr", "saferepr", "str"}
)

#: Callees known to CONSUME an environment argument without embedding it in
#: what they return. A ``CompletedProcess`` renders its args, return code and
#: output; a ``Popen`` its args and return code - never the ``env`` it was given.
#: Every other call this module cannot resolve is read as CARRYING a tainted
#: argument into its result, which is the direction that over-reports.
ENV_OPAQUE_SINKS: Final = frozenset({"Popen", "call", "check_call", "check_output", "run"})

#: Field names that carry an environment when read off an object that holds
#: one. Every other field of such an object is read as clean; the object itself
#: is always graded whole.
ENV_FIELD_NAMES: Final = frozenset(
    {"child_env", "env", "environ", "environment", "extra_env", "variables"}
)

#: The package whose modules are resolved and summarised. Test-SUPPORT code
#: lives here; production code under ``clockspeed/`` and ``tools/`` is the
#: subject of the assertions rather than a carrier between them, and a call into
#: it falls to the unresolved default like any other.
ENV_RESOLVED_PACKAGE: Final = "tests"


@dataclass(frozen=True)
class EnvSummary:
    """What one in-repo function's return carries, per parameter.

    Attributes:
        own: The return's kind with every parameter clean.
        through: Parameter name to the return's kind when THAT parameter alone
            holds an environment mapping.
        positional: Positional parameter names, in order.
        vararg: The ``*args`` name, if any.
        kwarg: The ``**kwargs`` name, if any.
    """

    own: int
    through: Mapping[str, int]
    positional: tuple[str, ...]
    vararg: str | None
    kwarg: str | None
    sealed: bool = False
    holder: bool = False

    def receiving(self, call: ast.Call, tainted: Callable[[ast.expr], bool]) -> set[str]:
        """The parameters a call hands a tainted argument to.

        Args:
            call: The call.
            tainted: Whether an argument expression carries the environment.

        Returns:
            The parameter names; every parameter for a tainted ``*`` or ``**``
            unpacking, whose destination cannot be read statically.
        """
        every = set(self.through)
        names: set[str] = set()
        for index, argument in enumerate(call.args):
            if not tainted(argument):
                continue
            if isinstance(argument, ast.Starred):
                return every
            if index < len(self.positional):
                names.add(self.positional[index])
            elif self.vararg is not None:
                names.add(self.vararg)
        for keyword in call.keywords:
            if not tainted(keyword.value):
                continue
            if keyword.arg is None:
                return every
            if keyword.arg in self.through:
                names.add(keyword.arg)
            elif self.kwarg is not None:
                names.add(self.kwarg)
        return names

    def result(self, call: ast.Call, tainted: Callable[[ast.expr], bool]) -> int:
        """What this call of the function returns.

        Args:
            call: The call.
            tainted: Whether an argument expression carries the environment.

        Returns:
            The kind.
        """
        carried = [self.through.get(name, ENV_CLEAN) for name in self.receiving(call, tainted)]
        return max([self.own, *carried])


#: The methods of a dict. Read off an environment MAPPING, any of these is a
#: value or a method object whose repr embeds the mapping; any other attribute
#: read off a mapping-kinded name is a FIELD of an object that name really
#: holds, graded by :data:`ENV_FIELD_NAMES`.
MAPPING_METHOD_NAMES: Final = frozenset(
    {
        "__getitem__",
        "copy",
        "get",
        "items",
        "keys",
        "pop",
        "popitem",
        "setdefault",
        "update",
        "values",
    }
)

#: Methods of a string, a path, a list or a dict that hand back content derived
#: from the receiver. Any OTHER method called on a value-kinded receiver is a
#: method of an object that holds the environment, and is read as returning
#: clean - a declared residual.
VALUE_CARRYING_METHODS: Final = frozenset(
    {
        "__getitem__",
        "absolute",
        "as_posix",
        "casefold",
        "center",
        "copy",
        "decode",
        "encode",
        "expandtabs",
        "format",
        "get",
        "items",
        "join",
        "joinpath",
        "ljust",
        "lower",
        "lstrip",
        "partition",
        "pop",
        "removeprefix",
        "removesuffix",
        "replace",
        "resolve",
        "rjust",
        "rpartition",
        "rsplit",
        "rstrip",
        "setdefault",
        "split",
        "splitlines",
        "strip",
        "swapcase",
        "title",
        "translate",
        "upper",
        "values",
        "with_name",
        "with_suffix",
        "zfill",
    }
)

#: Methods of a mapping that yield key NAMES or a flag, never a value.
MAPPING_NAME_METHODS: Final = frozenset({"__contains__", "__len__", "keys"})

#: Methods of a string value that yield a flag or a position, never the value.
VALUE_PREDICATE_METHODS: Final = frozenset(
    {
        "endswith",
        "find",
        "index",
        "isalnum",
        "isalpha",
        "isdecimal",
        "isdigit",
        "isidentifier",
        "islower",
        "isnumeric",
        "isspace",
        "isupper",
        "rfind",
        "rindex",
        "startswith",
    }
)

#: Methods that pour an argument INTO their receiver, so a receiver named by a
#: plain name becomes tainted by a tainted argument.
MUTATING_METHODS: Final = frozenset(
    {"add", "append", "extend", "insert", "setdefault", "update", "__setitem__"}
)


@dataclass(frozen=True)
class EnvFinding:
    """One assertion whose failure report would render an environment value.

    Attributes:
        module: Repo-relative path of the asserting file.
        lineno: The line of the offending sub-expression.
        channel: ``expression`` for a rewritten sub-expression, ``message`` for
            the assertion message.
        source: The offending sub-expression, unparsed. Repo SOURCE TEXT, never
            a runtime value - nothing in this module reads a value.
    """

    module: str
    lineno: int
    channel: str
    source: str


def describe_env_findings(findings: Sequence[EnvFinding]) -> str:
    """Render findings as file, line, channel and shape.

    Args:
        findings: What to render.

    Returns:
        One indented line each, sorted, carrying source text only.
    """
    return "\n".join(
        sorted(f"  {f.module}:{f.lineno}  [{f.channel}]  `{f.source}`" for f in findings)
    )


def _env_callee_name(call: ast.Call) -> str | None:
    """The bare name of whatever a call calls.

    Args:
        call: The call node.

    Returns:
        The function name, the method name, or None.
    """
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _env_iterated(kind: int) -> int:
    """What one element of an iteration over a value of this kind carries.

    Args:
        kind: The iterated value's kind.

    Returns:
        CLEAN over a mapping (key names), VALUE over values or over a sealed
        holder, whose iteration yields its fields.
    """
    return ENV_VALUE if kind in (ENV_VALUE, ENV_SEALED) else ENV_CLEAN


def _env_identity(target: ast.expr) -> Callable[[ast.expr], bool]:
    """A predicate true of exactly one argument node.

    Args:
        target: The node.

    Returns:
        The predicate.
    """

    def matches(node: ast.expr) -> bool:
        return node is target

    return matches


def env_renders(kind: int) -> bool:
    """Whether rendering a value of this kind prints environment content.

    Args:
        kind: The value's kind.

    Returns:
        True for a mapping or a value; False for clean and for a sealed holder.
    """
    return kind >= ENV_MAPPING


def _env_container(kinds: Sequence[int]) -> int:
    """What a literal container or a formatted string of these parts carries.

    Args:
        kinds: The parts' kinds.

    Returns:
        VALUE when any part renders, SEALED when a part only holds, else CLEAN.
    """
    if any(env_renders(kind) for kind in kinds):
        return ENV_VALUE
    return ENV_SEALED if ENV_SEALED in kinds else ENV_CLEAN


class _EnvScope:
    """The taint state of one lexical scope, and the grader over it.

    Args:
        environ_names: Bare names imported from ``os`` as the environment.
        functions: Callable name - a same-module function or one imported from
            an in-repo module - to its summary.
        inherited: Names bound tainted in an enclosing scope.
        modules: In-repo module alias, as spelled at the call site, to its
            functions' summaries.
    """

    def __init__(
        self,
        environ_names: frozenset[str],
        functions: Mapping[str, EnvSummary],
        inherited: Mapping[str, int],
        modules: Mapping[str, Mapping[str, EnvSummary]] | None = None,
    ) -> None:
        self.environ_names = environ_names
        self.functions = functions
        self.modules: Mapping[str, Mapping[str, EnvSummary]] = modules or {}
        self.bound: dict[str, int] = dict(inherited)
        #: Function name to parameter name to the strongest kind any call site
        #: in this module passed it - the REVERSE direction, read on a second
        #: pass so a helper's parameter is graded as what its callers hand it.
        self.callsites: dict[str, dict[str, int]] = {}
        self.returned = ENV_CLEAN

    # -- kinds --------------------------------------------------------------

    def kind(self, node: ast.AST | None) -> int:  # noqa: PLR0911, PLR0912
        """What environment content a node's VALUE carries.

        Args:
            node: The expression.

        Returns:
            CLEAN, MAPPING or VALUE.
        """
        if node is None:
            return ENV_CLEAN
        match node:
            case ast.Constant() | ast.Lambda() | ast.Compare():
                return ENV_CLEAN
            case ast.Attribute(attr=attr) if attr in ENVIRON_ATTRIBUTES:
                return ENV_MAPPING
            case ast.Attribute(value=value, attr=attr):
                return self._attribute_kind(value, attr)
            case ast.Name(id=name):
                if name in self.environ_names:
                    return ENV_MAPPING
                return self.bound.get(name, ENV_CLEAN)
            case ast.Subscript(value=value):
                return ENV_VALUE if self.kind(value) else ENV_CLEAN
            case ast.Call():
                return self._call_kind(node)
            case ast.Dict(keys=keys, values=values):
                if any(self.kind(key) for key in keys if key is not None):
                    return ENV_VALUE
                return ENV_MAPPING if any(self.kind(value) for value in values) else ENV_CLEAN
            case ast.List(elts=elts) | ast.Tuple(elts=elts) | ast.Set(elts=elts):
                return _env_container([self.kind(elt) for elt in elts])
            case ast.JoinedStr(values=values):
                return _env_container([self.kind(value) for value in values])
            case ast.FormattedValue(value=value):
                return _env_container([self.kind(value)])
            case ast.BinOp(left=left, op=op, right=right):
                kinds = (self.kind(left), self.kind(right))
                if isinstance(op, ast.BitOr) and ENV_MAPPING in kinds and ENV_VALUE not in kinds:
                    return ENV_MAPPING
                return ENV_VALUE if any(kinds) else ENV_CLEAN
            case ast.BoolOp(values=values):
                return max(self.kind(value) for value in values)
            case ast.IfExp(body=body, orelse=orelse):
                return max(self.kind(body), self.kind(orelse))
            case ast.UnaryOp(op=op, operand=operand):
                return ENV_CLEAN if isinstance(op, ast.Not) else self.kind(operand)
            case ast.NamedExpr(value=value) | ast.Starred(value=value) | ast.Await(value=value):
                return self.kind(value)
            case ast.ListComp() | ast.SetComp() | ast.GeneratorExp() | ast.DictComp():
                return self._comprehension_kind(node)
        return (
            ENV_VALUE
            if any(self.kind(child) for child in ast.iter_child_nodes(node))
            else ENV_CLEAN
        )

    def _attribute_kind(self, value: ast.expr, attr: str) -> int:
        """What reading one attribute off a value carries.

        A read off the environment MAPPING itself is a method object whose repr
        embeds the mapping. A read off anything else tainted - an object built
        from an environment argument, a parameter seeded in a summary - is a
        FIELD, and only a field named like an environment carries one: a
        ``Sandbox(env=..., git_dir=...)`` renders its ``env`` whole, while its
        ``git_dir`` is a path the environment never touched.

        Args:
            value: The receiver.
            attr: The attribute name.

        Returns:
            The kind.
        """
        receiver = self.kind(value)
        if receiver == ENV_MAPPING and attr in MAPPING_METHOD_NAMES:
            return ENV_VALUE
        if receiver and attr in ENV_FIELD_NAMES:
            return ENV_MAPPING
        return ENV_CLEAN

    def _record_call_site(self, name: str, summary: EnvSummary, call: ast.Call) -> None:
        """Remember what one call of a same-module function hands each parameter.

        Args:
            name: The function's name.
            summary: Its summary, for the parameter layout.
            call: The call.
        """
        seen = self.callsites.setdefault(name, {})
        for argument in (*call.args, *(keyword.value for keyword in call.keywords)):
            kind = self.kind(argument)
            if not kind:
                continue
            for parameter in summary.receiving(call, _env_identity(argument)):
                seen[parameter] = max(seen.get(parameter, ENV_CLEAN), kind)

    def annotation_kind(self, annotation: ast.expr | None) -> int:
        """What a value annotated this way carries, read off the class it names.

        A class with an environment-named field and NO hand-written ``__repr__``
        renders that field through its default repr, so a value of it is graded
        as a value; a class that seals itself is graded as a sealed holder.

        Args:
            annotation: A parameter's annotation, or None.

        Returns:
            The kind; CLEAN for an annotation naming no such class.
        """
        if annotation is None:
            return ENV_CLEAN
        summaries = [self.functions.get(word) for word in guard.annotation_names(annotation)]
        if isinstance(annotation, ast.Attribute):
            owner = self.modules.get(ast.unparse(annotation.value), {})
            summaries.append(owner.get(annotation.attr))
        kind = ENV_CLEAN
        for summary in summaries:
            if summary is not None and summary.holder:
                kind = max(kind, ENV_VALUE)
            elif summary is not None and summary.sealed:
                kind = max(kind, ENV_SEALED)
        return kind

    def _resolve(self, func: ast.expr) -> EnvSummary | None:
        """The summary of an in-repo function a call names, if it names one.

        Args:
            func: The call's callee expression.

        Returns:
            The summary, or None for a callee this module cannot resolve.
        """
        if isinstance(func, ast.Name):
            return self.functions.get(func.id)
        if isinstance(func, ast.Attribute):
            owner = self.modules.get(ast.unparse(func.value))
            if owner is not None:
                return owner.get(func.attr)
        return None

    def _call_kind(self, call: ast.Call) -> int:  # noqa: PLR0911, PLR0912
        """What a call's result carries.

        Args:
            call: The call.

        Returns:
            Its kind.
        """
        func = call.func
        name = _env_callee_name(call)
        if isinstance(func, ast.Attribute) and func.attr not in ENVIRON_ATTRIBUTES:
            receiver = self.kind(func.value)
            if receiver == ENV_MAPPING and func.attr in MAPPING_METHOD_NAMES:
                if func.attr in MAPPING_NAME_METHODS:
                    return ENV_CLEAN
                return ENV_MAPPING if func.attr == "copy" else ENV_VALUE
            if receiver == ENV_VALUE and func.attr in VALUE_CARRYING_METHODS:
                return ENV_VALUE
            if receiver and func.attr in ENV_FIELD_NAMES:
                return ENV_MAPPING
            if receiver:
                return ENV_CLEAN
        if name in ENVIRONMENT_READERS:
            return ENV_VALUE
        if (
            name == "getattr"
            and len(call.args) >= 2  # noqa: PLR2004 - getattr(owner, name)
            and isinstance(call.args[1], ast.Constant)
            and call.args[1].value in ENVIRON_ATTRIBUTES
        ):
            return ENV_MAPPING
        if name in MEASURE_REDUCERS:
            return ENV_CLEAN
        arguments = [*call.args, *(keyword.value for keyword in call.keywords)]
        carried = max((self.kind(argument) for argument in arguments), default=ENV_CLEAN)
        if name in ENV_PRESERVING:
            return carried
        if name in ENV_ITERATING:
            return _env_iterated(carried)
        if name in ENV_STRINGIFYING:
            return ENV_VALUE if env_renders(carried) else ENV_CLEAN
        summary = self._resolve(func)
        if summary is not None and summary.sealed:
            return ENV_SEALED if carried else ENV_CLEAN
        if summary is not None and summary.holder:
            return ENV_VALUE
        if summary is not None:
            if isinstance(func, ast.Name):
                self._record_call_site(func.id, summary, call)
            return summary.result(call, lambda argument: bool(self.kind(argument)))
        if name in ENV_OPAQUE_SINKS or (name is not None and not name[:1].isupper()):
            # A FUNCTION handed ``env=`` runs under it; a CONSTRUCTOR holds it.
            embedded = [
                *call.args,
                *(keyword.value for keyword in call.keywords if keyword.arg != "env"),
            ]
            carried = max((self.kind(argument) for argument in embedded), default=ENV_CLEAN)
        return ENV_VALUE if carried else ENV_CLEAN

    def _comprehension_kind(
        self, node: ast.ListComp | ast.SetComp | ast.GeneratorExp | ast.DictComp
    ) -> int:
        """What a comprehension's result carries.

        Args:
            node: The comprehension.

        Returns:
            Its kind.
        """
        saved = dict(self.bound)
        for generator in node.generators:
            self._bind_iteration(generator.target, generator.iter)
        if isinstance(node, ast.DictComp):
            value_kind = ENV_MAPPING if self.kind(node.value) else ENV_CLEAN
            result = ENV_VALUE if self.kind(node.key) else value_kind
        else:
            result = ENV_VALUE if self.kind(node.elt) else ENV_CLEAN
        self.bound = saved
        return result

    # -- binding ------------------------------------------------------------

    def taint(self, name: str, kind: int) -> None:
        """Bind a name, stickily - a tainted name never becomes clean.

        Args:
            name: The bound name.
            kind: What it now holds.
        """
        self.bound[name] = max(self.bound.get(name, ENV_CLEAN), kind)

    def _bind(self, target: ast.expr, kind: int, value: ast.expr | None = None) -> None:
        """Bind an assignment target.

        Args:
            target: The target expression.
            kind: What the assigned value carries.
            value: The assigned expression, for element-wise tuple unpacking.
        """
        match target:
            case ast.Name(id=name):
                self.taint(name, kind)
            case ast.Tuple(elts=elts) | ast.List(elts=elts):
                values = getattr(value, "elts", None)
                if values is not None and len(values) == len(elts):
                    for element, part in zip(elts, values, strict=True):
                        self._bind(element, self.kind(part), part)
                else:
                    for element in elts:
                        self._bind(element, _env_iterated(kind))
            case ast.Starred(value=inner):
                self._bind(inner, kind)
            case ast.Subscript(value=ast.Name(id=name)):
                self.taint(name, ENV_VALUE if kind else ENV_CLEAN)

    def _bind_iteration(self, target: ast.expr, iterable: ast.expr) -> None:
        """Bind a loop or comprehension target from what it iterates.

        ``for name, value in env.items()`` binds a key NAME and a VALUE.

        Args:
            target: The loop target.
            iterable: The iterated expression.
        """
        if (
            isinstance(iterable, ast.Call)
            and isinstance(iterable.func, ast.Attribute)
            and iterable.func.attr == "items"
            and self.kind(iterable.func.value) == ENV_MAPPING
            and isinstance(target, (ast.Tuple, ast.List))
            and len(target.elts) == 2  # noqa: PLR2004 - a (key, value) pair
        ):
            self._bind(target.elts[0], ENV_CLEAN)
            self._bind(target.elts[1], ENV_VALUE)
            return
        if (
            isinstance(iterable, ast.Call)
            and _env_callee_name(iterable) == "enumerate"
            and iterable.args
            and isinstance(target, (ast.Tuple, ast.List))
            and len(target.elts) == 2  # noqa: PLR2004 - an (index, element) pair
        ):
            self._bind(target.elts[0], ENV_CLEAN)
            self._bind(target.elts[1], _env_iterated(self.kind(iterable.args[0])))
            return
        if isinstance(iterable, (ast.Tuple, ast.List, ast.Set)):
            # A literal's elements keep their OWN kinds: a sealed holder
            # iterated out of ``(one, two)`` is still sealed.
            element = max((self.kind(elt) for elt in iterable.elts), default=ENV_CLEAN)
            self._bind(target, element)
            return
        self._bind(target, _env_iterated(self.kind(iterable)))

    def _bind_walruses(self, stmt: ast.stmt) -> None:
        """Bind every assignment expression inside one statement.

        Args:
            stmt: The statement.
        """
        for inner in ast.walk(stmt):
            if isinstance(inner, ast.NamedExpr):
                self._bind(inner.target, self.kind(inner.value))

    def _bind_mutation(self, call: ast.Call) -> None:
        """Taint a plain-named receiver that a mutating method pours a value into.

        ``env.update(os.environ)`` makes ``env`` carry the environment.

        Args:
            call: A call made as a bare statement.
        """
        func = call.func
        if not (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name)):
            return
        if func.attr not in MUTATING_METHODS:
            return
        arguments = [*call.args, *(keyword.value for keyword in call.keywords)]
        if any(self.kind(argument) for argument in arguments):
            self.taint(func.value.id, ENV_VALUE)

    def bind_statement(self, stmt: ast.stmt) -> None:
        """Apply every binding one statement makes.

        Args:
            stmt: The statement.
        """
        self._bind_walruses(stmt)
        match stmt:
            case ast.Assign(targets=targets, value=value):
                for target in targets:
                    self._bind(target, self.kind(value), value)
            case ast.AnnAssign(target=target, value=value) if value is not None:
                self._bind(target, self.kind(value), value)
            case ast.AugAssign(target=target, value=value):
                self._bind(target, self.kind(value), value)
            case ast.For(target=target, iter=iterable) | ast.AsyncFor(target=target, iter=iterable):
                self._bind_iteration(target, iterable)
            case ast.With(items=items) | ast.AsyncWith(items=items):
                for item in items:
                    if item.optional_vars is not None:
                        self._bind(item.optional_vars, self.kind(item.context_expr))
            case ast.Expr(value=ast.Call() as call):
                self._bind_mutation(call)
                # Evaluated for its side effect alone: a bare call is a call
                # site, and the reverse direction records what it hands over.
                self.kind(call)
            case ast.If(test=test) | ast.While(test=test):
                self.kind(test)
            case ast.Return(value=value) | ast.Expr(value=ast.Yield(value=value)):
                self.returned = max(self.returned, self.kind(value))

    # -- grading ------------------------------------------------------------

    def grade(self, stmt: ast.Assert, module: str, rewritten: bool) -> Iterator[EnvFinding]:
        """Every environment value one assertion's failure report renders.

        Args:
            stmt: The assertion.
            module: Repo-relative path, carried onto each finding.
            rewritten: Whether pytest rewrites this module.

        Yields:
            One finding per offending rendered sub-expression.
        """
        if rewritten:
            seen: set[int] = set()
            for node in explained(stmt.test):
                for part in (node, *rendered_parts(node)):
                    if id(part) in seen:
                        continue
                    seen.add(id(part))
                    if env_renders(self.kind(part)):
                        yield EnvFinding(module, part.lineno, "expression", ast.unparse(part))
        if stmt.msg is not None and env_renders(self.kind(stmt.msg)):
            yield EnvFinding(module, stmt.msg.lineno, "message", ast.unparse(stmt.msg))


def _environ_names(tree: ast.Module) -> frozenset[str]:
    """Bare names a module imports from ``os`` as the environment.

    Args:
        tree: The parsed module.

    Returns:
        ``environ`` for ``from os import environ``, or its alias.
    """
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "os":
            for alias in node.names:
                if alias.name in ENVIRON_ATTRIBUTES:
                    found.add(alias.asname or alias.name)
    return frozenset(found)


def _env_function_parameters(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.arg]:
    """Every named parameter of a function.

    Args:
        node: The function.

    Returns:
        The parameters, including ``*args`` and ``**kwargs``.
    """
    args = node.args
    extra = [arg for arg in (args.vararg, args.kwarg) if arg is not None]
    return [*args.posonlyargs, *args.args, *args.kwonlyargs, *extra]


def _env_parameter_defaults(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[tuple[ast.arg, ast.expr]]:
    """Each parameter that has a default, paired with it.

    Args:
        node: The function.

    Returns:
        The pairs.
    """
    args = node.args
    positional = [*args.posonlyargs, *args.args]
    pairs = list(
        zip(positional[len(positional) - len(args.defaults) :], args.defaults, strict=True)
    )
    pairs += [
        (arg, default)
        for arg, default in zip(args.kwonlyargs, args.kw_defaults, strict=True)
        if default is not None
    ]
    return pairs


def _env_walk_scope(
    scope: ast.AST,
    scope_state: _EnvScope,
    module: str,
    rewritten: bool,
    fixtures: Mapping[str, int],
    callsites: Mapping[str, Mapping[str, int]] | None = None,
) -> Iterator[EnvFinding]:
    """Grade every assertion in one scope, then in each scope nested in it.

    Args:
        scope: A module, function or class.
        scope_state: The scope's taint state, already seeded.
        module: Repo-relative path.
        rewritten: Whether pytest rewrites this module.
        fixtures: Same-module fixture name to the kind it provides.
        callsites: Function name to parameter name to what the module's call
            sites hand it, from a first pass; None on that first pass.

    Yields:
        Findings.
    """
    nested: list[ast.AST] = []
    for stmt in scope_statements(scope):
        if isinstance(stmt, (*ANY_FUNCTION, ast.ClassDef)):
            nested.append(stmt)
            continue
        scope_state.bind_statement(stmt)
        if isinstance(stmt, ast.Assert):
            yield from scope_state.grade(stmt, module, rewritten)
    for child in nested:
        inner = _EnvScope(
            scope_state.environ_names,
            scope_state.functions,
            scope_state.bound,
            scope_state.modules,
        )
        inner.callsites = scope_state.callsites
        if isinstance(child, ANY_FUNCTION):
            for arg in _env_function_parameters(child):
                if arg.arg in fixtures:
                    inner.taint(arg.arg, fixtures[arg.arg])
                inner.taint(arg.arg, inner.annotation_kind(arg.annotation))
                inner.taint(arg.arg, (callsites or {}).get(child.name, {}).get(arg.arg, 0))
            for arg, default in _env_parameter_defaults(child):
                inner.taint(arg.arg, inner.kind(default))
        yield from _env_walk_scope(child, inner, module, rewritten, fixtures, callsites)


def _env_is_fixture(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Whether a function is declared a pytest fixture.

    Args:
        node: The function.

    Returns:
        True for any spelling of the decorator, bare or called.
    """
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target, ast.Attribute) and target.attr == "fixture":
            return True
        if isinstance(target, ast.Name) and target.id == "fixture":
            return True
    return False


def _env_returned(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    environ_names: frozenset[str],
    functions: Mapping[str, EnvSummary],
    modules: Mapping[str, Mapping[str, EnvSummary]],
    seeded: Mapping[str, int],
) -> int:
    """What one function's return carries, with some parameters seeded.

    Args:
        node: The function.
        environ_names: Bare names imported as the environment.
        functions: Callable summaries known so far.
        modules: In-repo module aliases to their summaries.
        seeded: Parameter name to the kind it is seeded with.

    Returns:
        The return kind.
    """
    state = _EnvScope(environ_names, functions, seeded, modules)
    for stmt in scope_statements(node):
        if not isinstance(stmt, (*ANY_FUNCTION, ast.ClassDef)):
            state.bind_statement(stmt)
    return state.returned


def _env_summarise(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    environ_names: frozenset[str],
    functions: Mapping[str, EnvSummary],
    modules: Mapping[str, Mapping[str, EnvSummary]],
) -> EnvSummary:
    """One function's summary under the summaries known so far.

    Args:
        node: The function.
        environ_names: Bare names imported as the environment.
        functions: Callable summaries known so far.
        modules: In-repo module aliases to their summaries.

    Returns:
        The summary.
    """
    args = node.args
    names = [arg.arg for arg in _env_function_parameters(node)]
    probe = _EnvScope(environ_names, functions, {}, modules)
    annotated = {
        arg.arg: kind
        for arg in _env_function_parameters(node)
        if (kind := probe.annotation_kind(arg.annotation))
    }
    through = {
        name: _env_returned(
            node, environ_names, functions, modules, {**annotated, name: ENV_MAPPING}
        )
        or _env_returned(node, environ_names, functions, modules, {**annotated, name: ENV_VALUE})
        for name in names
    }
    return EnvSummary(
        own=_env_returned(node, environ_names, functions, modules, annotated),
        through=through,
        positional=tuple(arg.arg for arg in (*args.posonlyargs, *args.args)),
        vararg=args.vararg.arg if args.vararg is not None else None,
        kwarg=args.kwarg.arg if args.kwarg is not None else None,
    )


def _env_join(old: EnvSummary, new: EnvSummary) -> EnvSummary:
    """The pointwise maximum of two summaries of one function.

    Args:
        old: The summary so far.
        new: A fresh evaluation.

    Returns:
        The join, so the fixpoint only ever rises.
    """
    through = {
        name: max(old.through.get(name, ENV_CLEAN), kind) for name, kind in new.through.items()
    }
    return EnvSummary(
        max(old.own, new.own), through, new.positional, new.vararg, new.kwarg, old.sealed
    )


def _env_return_kinds(
    tree: ast.Module,
    environ_names: frozenset[str],
    imported: Mapping[str, EnvSummary] | None = None,
    modules: Mapping[str, Mapping[str, EnvSummary]] | None = None,
) -> tuple[dict[str, EnvSummary], dict[str, int]]:
    """Summarise every module-level function, to a fixpoint.

    EVERY function gets a summary, clean ones included, so a call to a clean
    in-repo function resolves to clean instead of falling to the unresolved
    default, which reads a tainted argument as carried.

    Args:
        tree: The parsed module.
        environ_names: Bare names imported as the environment.
        imported: Summaries of callables imported from in-repo modules.
        modules: In-repo module aliases to their summaries.

    Returns:
        Function name to its summary, and fixture name to the kind it provides
        for the tainted fixtures only.
    """
    functions = [node for node in tree.body if isinstance(node, ANY_FUNCTION)]
    aliases = modules or {}
    known: dict[str, EnvSummary] = dict(imported or {})
    for node in functions:
        known[node.name] = EnvSummary(ENV_CLEAN, {}, (), None, None)
    for statement in tree.body:
        if not isinstance(statement, ast.ClassDef):
            continue
        if guard.repr_method(statement) is not None:
            known[statement.name] = EnvSummary(ENV_CLEAN, {}, (), None, None, sealed=True)
        elif set(guard.declared_fields(statement)) & ENV_FIELD_NAMES:
            known[statement.name] = EnvSummary(ENV_CLEAN, {}, (), None, None, holder=True)
    for _ in range(2 * len(functions) + 2):
        changed = False
        for node in functions:
            joined = _env_join(
                known[node.name], _env_summarise(node, environ_names, known, aliases)
            )
            if joined != known[node.name]:
                known[node.name] = joined
                changed = True
        if not changed:
            break
    fixtures = {
        node.name: known[node.name].own
        for node in functions
        if known[node.name].own and _env_is_fixture(node)
    }
    return known, fixtures


def _env_module_file(root: Path, dotted: str) -> str | None:
    """The in-repo source file a dotted module name resolves to.

    Args:
        root: The repository root.
        dotted: The module's dotted name.

    Returns:
        Its repo-relative path, or None for anything outside the repository.
    """
    if dotted.split(".", 1)[0] != ENV_RESOLVED_PACKAGE:
        return None
    base = "/".join(dotted.split("."))
    for relative in (f"{base}.py", f"{base}/__init__.py"):
        if (root / relative).is_file():
            return relative
    return None


def _env_package_of(module: str, level: int) -> str:
    """The dotted package a relative import of this level is anchored at.

    Args:
        module: Repo-relative path of the importing file.
        level: The number of leading dots.

    Returns:
        The dotted package name, possibly empty.
    """
    parts = module.split("/")[:-1]
    if level > 1:
        parts = parts[: len(parts) - (level - 1)]
    return ".".join(parts)


#: Modules whose summary is being computed, so an import cycle reads as an
#: empty summary rather than recursing without bound.
_ENV_IN_PROGRESS: set[tuple[str, str]] = set()


@cache
def _env_module_summary(root: str, module: str) -> Mapping[str, EnvSummary]:
    """Every function summary of one in-repo module, imports resolved.

    Args:
        root: The repository root, as a string so the cache can key it.
        module: Repo-relative path of the module.

    Returns:
        Function name to summary; empty for a module in an import cycle or one
        that does not parse.
    """
    key = (root, module)
    if key in _ENV_IN_PROGRESS:
        return {}
    _ENV_IN_PROGRESS.add(key)
    try:
        tree = ast.parse((Path(root) / module).read_bytes())
    except (OSError, SyntaxError, ValueError):
        return {}
    else:
        environ_names = _environ_names(tree)
        imported, modules = _env_resolve_imports(tree, module, Path(root))
        return _env_return_kinds(tree, environ_names, imported, modules)[0]
    finally:
        _ENV_IN_PROGRESS.discard(key)


def _env_resolve_imports(
    tree: ast.Module, module: str, root: Path
) -> tuple[dict[str, EnvSummary], dict[str, Mapping[str, EnvSummary]]]:
    """Resolve a module's imports of in-repo code to function summaries.

    Handles ``from tests.x import f``, ``from .x import f``, ``from tests
    import x`` and ``import tests.x`` with or without ``as``.

    Args:
        tree: The parsed importing module.
        module: Its repo-relative path.
        root: The repository root.

    Returns:
        Imported callable name to summary, and module alias as spelled at a
        call site to that module's summaries.
    """
    imported: dict[str, EnvSummary] = {}
    modules: dict[str, Mapping[str, EnvSummary]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found = _env_module_file(root, alias.name)
                if found is not None:
                    modules[alias.asname or alias.name] = _env_module_summary(str(root), found)
        elif isinstance(node, ast.ImportFrom):
            package = node.module or ""
            if node.level:
                anchor = _env_package_of(module, node.level)
                package = ".".join(part for part in (anchor, package) if part)
            source = _env_module_file(root, package)
            for alias in node.names:
                bound = alias.asname or alias.name
                submodule = _env_module_file(root, f"{package}.{alias.name}".strip("."))
                if submodule is not None:
                    modules[bound] = _env_module_summary(str(root), submodule)
                elif source is not None:
                    summary = _env_module_summary(str(root), source).get(alias.name)
                    if summary is not None:
                        imported[bound] = summary
    return imported, modules


def is_rewritten_module(module: str) -> bool:
    """Whether pytest rewrites a module's assertions on this project.

    No module calls ``register_assert_rewrite``, so the set is exactly the
    collected test modules plus conftest files under ``tests/``.

    Args:
        module: Repo-relative, forward-slashed path.

    Returns:
        True for ``tests/**/test_*.py``, ``tests/**/*_test.py`` and
        ``tests/**/conftest.py``.
    """
    if not module.startswith("tests/"):
        return False
    name = module.rsplit("/", 1)[-1]
    return name == "conftest.py" or name.startswith("test_") or name.endswith("_test.py")


def scan_env_source(module: str, source: str, root: Path = REPO_ROOT) -> list[EnvFinding]:
    """Every environment-rendering assertion in one module's source.

    Args:
        module: Repo-relative path; decides whether the expression channel
            applies and anchors relative imports.
        source: The module's text.
        root: The tree imports are resolved against.

    Returns:
        The findings, in source order.
    """
    tree = ast.parse(source)
    environ_names = _environ_names(tree)
    imported, modules = _env_resolve_imports(tree, module, root)
    functions, fixtures = _env_return_kinds(tree, environ_names, imported, modules)
    rewritten = is_rewritten_module(module)
    collector = _EnvScope(environ_names, functions, {}, modules)
    for _ in _env_walk_scope(tree, collector, module, rewritten, fixtures):
        pass
    state = _EnvScope(environ_names, functions, {}, modules)
    found = list(_env_walk_scope(tree, state, module, rewritten, fixtures, collector.callsites))
    return sorted(found, key=lambda finding: (finding.lineno, finding.source))


@cache
def scan_env_repo() -> tuple[EnvFinding, ...]:
    """Every environment-rendering assertion in the tracked tree.

    Returns:
        The findings.
    """
    found: list[EnvFinding] = []
    for module in tracked_python_files():
        path = REPO_ROOT / module
        if not path.is_file():
            continue
        found += scan_env_source(module, path.read_text(encoding="utf-8"))
    return tuple(found)


# ---------------------------------------------------------------------------
# The tree is clean
# ---------------------------------------------------------------------------


def test_no_assertion_renders_an_environment_value() -> None:
    findings = scan_env_repo()
    count = len(findings)
    listing = describe_env_findings(findings)
    assert count == 0, (
        f"{count} assertion(s) would render a process-environment value into a failure"
        f" report. Bind the KEY NAMES of what changed to a list first:\n{listing}"
    )


def test_the_sweep_graded_a_real_population() -> None:
    graded = sum(1 for module in tracked_python_files() if is_rewritten_module(module))
    assert graded > 100, f"only {graded} rewritten modules were found to grade"  # noqa: PLR2004


# ---------------------------------------------------------------------------
# The shapes, pinned - flagged and not flagged
# ---------------------------------------------------------------------------

_ENV_REWRITTEN: Final = "tests/test_synthetic.py"
_ENV_PLAIN: Final = "tests/synthetic_helper.py"


def _env_lines(source: str, module: str = _ENV_REWRITTEN) -> list[tuple[int, str]]:
    """The (line, channel) pairs a synthetic module is flagged at.

    Args:
        source: The synthetic module.
        module: The path it pretends to live at.

    Returns:
        The pairs, in source order.
    """
    return [(finding.lineno, finding.channel) for finding in scan_env_source(module, source)]


def test_the_cs1199_shape_is_flagged_at_its_line() -> None:
    source = (
        "import os\n"
        "def test_walk():\n"
        "    before = dict(os.environ)\n"
        "    walk()\n"
        "    assert dict(os.environ) == before\n"
    )
    flagged = _env_lines(source)
    assert (5, "expression") in flagged, f"the dict(os.environ) == before shape passed: {flagged}"


def test_a_membership_test_against_the_environment_is_flagged() -> None:
    # MEASURED: visit_Attribute reprs os.environ itself, so this renders the
    # whole environment. The behavioural arm below re-measures it every run.
    source = 'import os\ndef test_x():\n    assert "X" not in os.environ\n'
    assert _env_lines(source) == [(3, "expression")]


def test_a_reduction_over_the_environment_still_renders_its_argument() -> None:
    source = "import os\ndef test_x():\n    assert len(os.environ) > 0\n"
    assert _env_lines(source) == [(3, "expression")]


def test_a_single_value_read_is_flagged() -> None:
    for read in ('os.environ.get("X")', 'os.getenv("X")', 'os.environ["X"]'):
        source = f'import os\ndef test_x():\n    assert {read} == "v"\n'
        count = len(_env_lines(source))
        assert count > 0, f"a value read passed unflagged: {read}"


def test_every_binding_form_carries_the_taint() -> None:
    bindings = (
        "env = os.environ.copy()",
        "env = {**os.environ}",
        "env, other = dict(os.environ), 1",
        "if (env := dict(os.environ)): pass",
        "env = {}\n    env.update(os.environ)",
        "env = {}\n    env['k'] = os.environ['k']",
        "for _, env in os.environ.items(): pass",
        "env = [v for v in os.environ.values()]",
    )
    for binding in bindings:
        source = f"import os\ndef test_x():\n    {binding}\n    assert env == 1\n"
        count = len(_env_lines(source))
        assert count > 0, f"a binding form dropped the taint: {binding}"


def test_an_imported_alias_and_a_same_module_helper_are_followed() -> None:
    aliased = "from os import environ as e\ndef test_x():\n    assert e == {}\n"
    helper = (
        "import os\n"
        "def _snapshot():\n"
        "    return dict(os.environ)\n"
        "def test_x():\n"
        "    assert _snapshot() == {}\n"
    )
    fixture = (
        "import os, pytest\n"
        "@pytest.fixture\n"
        "def env():\n"
        "    return dict(os.environ)\n"
        "def test_x(env):\n"
        "    assert env == {}\n"
    )
    assert _env_lines(aliased) == [(3, "expression")]
    assert _env_lines(helper) == [(5, "expression")]
    assert _env_lines(fixture) == [(6, "expression")]


def test_the_message_channel_is_graded_even_where_nothing_is_rewritten() -> None:
    source = 'import os\ndef check():\n    env = dict(os.environ)\n    assert not env, f"{env}"\n'
    assert _env_lines(source, _ENV_PLAIN) == [(4, "message")]
    assert _env_lines(source) == [(4, "expression"), (4, "message")]


def test_the_expression_channel_is_not_graded_where_pytest_does_not_rewrite() -> None:
    source = "import os\ndef check():\n    assert dict(os.environ) == {}\n"
    assert _env_lines(source, _ENV_PLAIN) == []


def test_the_remedies_are_not_flagged() -> None:
    remedies = (
        # key NAMES of what changed, bound before the assert
        "before = dict(os.environ)\n"
        "    walk()\n"
        "    after = dict(os.environ)\n"
        "    changed = sorted(k for k in set(before) | set(after)"
        " if before.get(k) != after.get(k))\n"
        '    assert changed == [], f"changed: {changed}"',
        # a membership bound to a bool
        'present = "X" in os.environ\n    assert not present, "X is set"',
        # names only
        'names = sorted(os.environ)\n    assert "X" in names',
        'names = set(os.environ.keys())\n    assert "X" not in names',
        "count = len(os.environ)\n    assert count > 0",
        # the loop variable over items() that holds the NAME
        "for name, _ in os.environ.items():\n        assert name",
    )
    for remedy in remedies:
        source = f"import os\ndef test_x():\n    {remedy}\n"
        flagged = _env_lines(source)
        assert flagged == [], f"a remedy was flagged at {flagged}:\n{remedy}"


def test_an_unrelated_dict_and_a_subprocess_result_are_not_flagged() -> None:
    source = (
        "import os, subprocess\n"
        "def test_x():\n"
        "    env = dict(os.environ)\n"
        "    result = subprocess.run(['x'], env=env)\n"
        "    other = {'a': 1}\n"
        "    assert result.returncode == 0\n"
        "    assert other == {'a': 1}\n"
    )
    assert _env_lines(source) == []


#: A synthetic test-support module, shaped like ``tests/git_env.py``.
_ENV_HELPER: Final = (
    "import os, subprocess\n"
    "def scrub(env):\n"
    "    return {k: v for k, v in env.items() if not k.startswith('GIT_')}\n"
    "def scrubbed_env():\n"
    "    return scrub(dict(os.environ))\n"
    "def plain_git(*args, cwd, env):\n"
    "    return subprocess.run(['git', *args], cwd=cwd, env=env)\n"
    "class Sealed:\n"
    "    def __init__(self, env):\n"
    "        self.env = env\n"
    "    def __repr__(self):\n"
    "        return 'Sealed(<withheld>)'\n"
)


def _env_tree_lines(tmp_path: Path, body: str) -> list[tuple[int, str]]:
    """Flag a synthetic test module that imports from a synthetic helper.

    Args:
        tmp_path: The synthetic repository root.
        body: The test module's source.

    Returns:
        The (line, channel) pairs it is flagged at.
    """
    helpers = tmp_path / "tests"
    helpers.mkdir(exist_ok=True)
    (helpers / "__init__.py").write_bytes(b"")
    (helpers / "git_helper.py").write_bytes(_ENV_HELPER.encode("ascii"))
    findings = scan_env_source("tests/test_synthetic.py", body, root=tmp_path)
    return [(finding.lineno, finding.channel) for finding in findings]


def test_a_helper_imported_from_a_support_module_is_resolved(tmp_path: Path) -> None:
    # The refuted shape: tests/test_git_env_scrub.py read scrubbed_env() clean.
    spellings = (
        ("from tests.git_helper import plain_git, scrubbed_env\n", "scrubbed_env"),
        ("from .git_helper import plain_git, scrubbed_env\n", "scrubbed_env"),
        ("from tests.git_helper import plain_git, scrubbed_env as carrier\n", "carrier"),
    )
    for spelling, carrier in spellings:
        body = (
            f"{spelling}"
            "def test_x():\n"
            f"    assert plain_git('init', cwd='.', env={carrier}()).returncode == 0\n"
        )
        line = body.count("\n")
        flagged = _env_tree_lines(tmp_path, body)
        assert (line, "expression") in flagged, f"an imported carrier passed: {spelling!r}"


def test_a_module_alias_call_is_resolved(tmp_path: Path) -> None:
    for spelling, prefix in (
        ("import tests.git_helper as h\n", "h"),
        ("import tests.git_helper\n", "tests.git_helper"),
        ("from tests import git_helper\n", "git_helper"),
    ):
        body = f"{spelling}def test_x():\n    assert {prefix}.scrubbed_env() == {{}}\n"
        flagged = _env_tree_lines(tmp_path, body)
        assert flagged == [(3, "expression")], f"a module alias call passed: {spelling!r}"


def test_a_parameter_is_carried_only_where_the_helper_returns_it(tmp_path: Path) -> None:
    body = (
        "import os\n"
        "from tests.git_helper import plain_git, scrub\n"
        "def test_x():\n"
        "    leaky = dict(os.environ)\n"
        "    scrubbed = scrub(leaky)\n"
        "    done = plain_git('status', cwd='.', env=leaky)\n"
        "    assert done.returncode == 0\n"
        "    assert scrubbed == {}\n"
    )
    assert _env_tree_lines(tmp_path, body) == [(8, "expression")]


def test_a_sealed_holder_renders_clean_and_its_env_field_does_not(tmp_path: Path) -> None:
    body = (
        "import os\n"
        "from tests.git_helper import Sealed\n"
        "def test_x():\n"
        "    box = Sealed(env=dict(os.environ))\n"
        "    assert box is None\n"
        "    assert box.env == {}\n"
    )
    assert _env_tree_lines(tmp_path, body) == [(6, "expression")]


def test_an_unresolved_call_carries_a_tainted_argument() -> None:
    carriers = (
        "wrap(os.environ)",
        "Holder(env=dict(os.environ))",
        "json.dumps(dict(os.environ))",
        "pprint.pformat(dict(os.environ))",
        'getattr(os, "environ")',
    )
    for carrier in carriers:
        source = f"import os\ndef test_x():\n    held = {carrier}\n    assert held == 1\n"
        count = len(_env_lines(source))
        assert count > 0, f"an unresolved carrier passed: {carrier}"


#: A holder with an environment field and the DEFAULT repr, beside one that
#: seals itself - the HookLayout shape of the second refutation.
_ENV_HOLDERS: Final = (
    "import os\n"
    "from typing import NamedTuple\n"
    "class Layout(NamedTuple):\n"
    "    root: str\n"
    "    env: dict\n"
    "class Carrier(NamedTuple):\n"
    "    root: str\n"
    "    env: dict\n"
    "    def __repr__(self):\n"
    "        return 'Carrier(<withheld>)'\n"
)


def test_a_parameter_annotated_with_an_unsealed_holder_is_graded() -> None:
    source = (
        f"{_ENV_HOLDERS}"
        "def check(layout: Layout, carrier: Carrier) -> None:\n"
        "    assert layout.root\n"
        "    assert carrier.root\n"
        "    assert carrier.env == {}\n"
    )
    assert _env_lines(source) == [(12, "expression"), (14, "expression")]


def test_an_unsealed_holder_built_from_nothing_tainted_is_still_graded() -> None:
    source = f"{_ENV_HOLDERS}def test_x():\n    made = Layout('r', {{}})\n    assert made.root\n"
    assert _env_lines(source) == [(13, "expression")]


def test_a_parameter_is_graded_as_what_its_call_sites_hand_it() -> None:
    source = (
        "import os\n"
        "def check(env, name):\n"
        "    assert env.get(name, '').endswith('x')\n"
        "    assert name\n"
        "def test_x():\n"
        "    check(dict(os.environ), 'HOME')\n"
    )
    assert sorted(set(_env_lines(source))) == [(3, "expression")]


def test_a_sealed_holder_iterated_out_of_a_literal_stays_sealed() -> None:
    source = (
        f"{_ENV_HOLDERS}"
        "def check(one: Carrier, two: Carrier) -> None:\n"
        "    for run in (one, two):\n"
        "        assert run.root\n"
    )
    assert _env_lines(source) == []


def test_a_function_handed_env_runs_under_it_rather_than_returning_it() -> None:
    source = (
        "import os\n"
        "def test_x():\n"
        "    row = ladder_row('.', env=dict(os.environ))\n"
        "    assert row['ok']\n"
    )
    assert _env_lines(source) == []


# ---------------------------------------------------------------------------
# The channel, measured under real pytest every run
# ---------------------------------------------------------------------------

#: A synthetic token planted in the CHILD's environment only. It never exists in
#: this process's environment, so nothing real is rendered by this arm.
_ENV_PLANT: Final = "CS1199PLANTEDTOKEN"

_ENV_PROBE: Final = (
    "import os\n"
    "\n"
    "def test_flagged():\n"
    '    assert "CS1199_ABSENT" in os.environ\n'
    "\n"
    "def test_remedied():\n"
    '    present = "CS1199_ABSENT" in os.environ\n'
    '    assert present, "CS1199_ABSENT is not set"\n'
)


def _env_render(tmp_path: Path, test: str) -> tuple[int, int]:
    """Run one probe test in a child pytest; count the plant in its report.

    Args:
        tmp_path: Where the probe module and an empty ini are written.
        test: The probe test's name.

    Returns:
        The child's exit code and how many times the plant was rendered.
    """
    kept = ("PATH", "SYSTEMROOT", "TEMP", "TMP", "HOME", "USERPROFILE")
    child_env = {key: os.environ[key] for key in kept if key in os.environ}
    child_env["CS1199_PLANT"] = _ENV_PLANT
    child_env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "-c",
            str(tmp_path / "pytest.ini"),
            "--rootdir",
            str(tmp_path),
            f"{tmp_path / 'test_probe.py'}::{test}",
        ],
        cwd=tmp_path,
        env=child_env,
        capture_output=True,
        check=False,
        timeout=120,
    )
    rendered = result.stdout.decode("utf-8", errors="replace")
    return result.returncode, rendered.count(_ENV_PLANT)


def test_the_flagged_shape_renders_the_environment_and_the_remedy_does_not(
    tmp_path: Path,
) -> None:
    (tmp_path / "pytest.ini").write_bytes(b"[pytest]\n")
    (tmp_path / "test_probe.py").write_bytes(_ENV_PROBE.encode("ascii"))
    flagged_exit, flagged_count = _env_render(tmp_path, "test_flagged")
    remedied_exit, remedied_count = _env_render(tmp_path, "test_remedied")
    assert flagged_exit == 1, "the flagged probe did not fail, so it rendered nothing"
    assert remedied_exit == 1, "the remedied probe did not fail, so it rendered nothing"
    assert flagged_count > 0, "the flagged shape no longer renders the environment"
    assert remedied_count == 0, "the remedy still renders the environment"
    lines = [(f.lineno, f.channel) for f in scan_env_source("tests/test_probe.py", _ENV_PROBE)]
    assert lines == [(4, "expression")], f"the guard does not agree with pytest: {lines}"
