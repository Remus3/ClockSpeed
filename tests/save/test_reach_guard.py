"""The controls that grade the library-reach guard, CS-491 and CS-495.

THE GUARD ITSELF LIVES IN ``tests/save/reach_guard.py``. This module holds the
claims about it: nothing here is imported by the guard, and the guard is
imported by everything here.

THE SENTENCE THAT USED TO OPEN THIS FILE SAID THE GUARD LIVED IN
``test_properties.py`` AND STAYED THERE. It was true when session 24 wrote it
and CS-495 made it false on purpose - the paragraph below it already recorded
that the objection behind "stays there" no longer held. The objection was that
``test_every_library_reaching_function_here_is_declared`` needs the guard's
owner inside the guard's own scope, since a guard whose owner sits outside it is
the arrangement that let a third sweep ship ungraded one file over. CS-471's
package walk globs ``*.py`` rather than test modules, so ``reach_guard`` is
graded by the guard it defines, and the property is preserved by the move rather
than broken by it.

WHY BOTH MOVES HAPPENED is recorded once, in ``tests/save/reach_guard.py``'s
module docstring, and is not restated here.

EVERY CONTROL HERE PLANTS INTO ``tmp_path`` AND NEEDS NO SAVE LIBRARY. They are
claims about the repository, not about a world, so they run identically on a
machine with no game installed - which is where they were measured.

WHAT THEY GRADE, in one line each: that a primitive reached through an alias, a
wrapper, a subscript, a string or a compound-statement scope is NAMED by the
guard; that a module reaching only through a sibling is not classed silent; that
a sibling's EXEMPT helper exports no reach it does not have; that a body handed
back in another shape propagates; that the guard's own failure message carries
function names and never a path; that the primitive vocabulary is partitioned
without a leftover; that a module reaching the library and declaring nothing is
caught; that a declaration outliving its code is caught; and that the gutting
guard beside it catches a test spliced to an early return.

WHAT IS NOT HERE, and deliberately. A module that CONSUMES the guard keeps the
checks that grade ITS OWN source: its reaching functions declared, and an
uncontained helper spliced into a copy of that source caught. Those grade the
module, not the guard, and moving them here would have graded one file in the
name of the package.

THAT SENTENCE SAID "THREE CHECKS" AND NAMED A GUTTING CHECK AS THE THIRD, AND A
REFUTATION PASS MEASURED IT FALSE: of the five modules that self-apply the reach
guard, only two call ``_assert_no_test_is_gutted`` at all. It is not a rule the
package follows, it is a habit two modules have. Corrected rather than made true
by adding the check to three more modules, which would be a different item. It
also carried a module COUNT, which was stale in the direction that reads as
smaller; CLAUDE.md section 4 forbids the number here, so it is gone rather than
re-measured.
"""

from __future__ import annotations

import ast
import importlib
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from tests.save import reach_guard
from tests.save.reach_guard import (
    _FILESYSTEM_PRIMITIVES,
    _LIBRARY_LOCATORS,
    _LIBRARY_PRIMITIVES,
    _NOT_LIBRARY_REACH,
    _PERSONAL_DATA_TYPES,
    _REACH_DECLARATIONS,
    _REACHES_THE_LIBRARY,
    MODULE_SCOPE_REACH,
    _assert_library_reach_is_declared,
    _assert_no_test_is_gutted,
    _body_wrapping_classes,
    _calls_any,
    _carries_personal_data,
    _declaration_verdicts,
    _effective_primitives,
    _imported_sibling,
    _module_reaches,
    _module_scope_reaches,
    _personal_data_names,
    _reach_primitives,
    _reaching_modules,
    _returns_personal_data,
    _scanned_functions,
    _stands_for_a_primitive,
)

#: A declared, graded reach site planted BESIDE every CS-491 route.
#:
#: WHY IT IS HERE, AND THE PART OF THAT REASON THAT WAS MEASURED FALSE. It was
#: added because the first draft of this matrix had no companion and every route
#: reddened on the guard's own vacuity assertion - ``no function here touches a
#: library primitive`` - a red that says nothing whatever about the route. That
#: happened, and it is why the companion exists.
#:
#: WHAT WAS FALSE was the present-tense claim that its presence is what makes
#: these controls measure the route. A refutation pass replanted every route
#: WITHOUT the companion and the suite stayed green: under the WIDENED guard
#: each route lands in ``direct``, so the vacuity assertion cannot fire and the
#: declaration assertion raises first, naming the evader. The sentence was true
#: of the guard as it stood before CS-491 and false of the one it ships with.
#: The companion is kept because a control should not depend on which assertion
#: happens to fire first, and because a future narrowing would reinstate exactly
#: the red it was added to avoid.
_DECLARED_COMPANION: Final = '''
from clockspeed.data import locate


def _declared_reach() -> list:
    """The planted module's honest, declared reach site."""
    root = locate.resolve_save_root()
    return sorted(locate.resolve_account_dir(root).glob("*.sav"))
'''

#: What the companion is declared as, so the guard has something to accept. Its
#: return annotation is deliberately NOT personal data, so the direct-route
#: controls below cannot be satisfied by the propagation half instead.
_COMPANION_GRADED: Final = MappingProxyType(
    {"_declared_reach": "the planted module's own declared reach site"}
)

#: Reach routes that spell no primitive in any callee position, as label mapped
#: to the source to plant and the name the guard's failure has to report.
#:
#: EVERY ENTRY WAS MEASURED PAST THE POST-CS-471 GUARD, by refutation passes and
#: then again by the merger before any of this was written. None is a shape
#: imagined from the implementation. Three root causes are represented: an alias
#: expansion that resolved only a bare name or attribute at MODULE scope, a
#: ``getattr`` whose second argument was read only as a literal, and a callee
#: position that was never read through when it was itself a call.
_ALIASED_REACH_ROUTES: Final = MappingProxyType(
    {
        "module-scope-lambda": (
            "\n\n_find = lambda: locate.resolve_save_root()\n"
            "\n\ndef _reaches_through_a_lambda():\n"
            '    """Reaches the locator through a module-scope lambda."""\n'
            "    return _find()\n",
            "_reaches_through_a_lambda",
        ),
        "functools-partial": (
            "\n\nimport functools\n"
            "\n_find = functools.partial(locate.resolve_save_root)\n"
            "\n\ndef _reaches_through_partial():\n"
            '    """Reaches the locator through a partial that names it as an argument."""\n'
            "    return _find()\n",
            "_reaches_through_partial",
        ),
        "bound-methodcaller": (
            "\n\nimport operator\n"
            '\n_glob = operator.methodcaller("glob", "*.sav")\n'
            "\n\ndef _reaches_through_a_bound_methodcaller(account):\n"
            '    """Reaches the glob through a methodcaller bound at module scope."""\n'
            "    return sorted(_glob(account))\n",
            "_reaches_through_a_bound_methodcaller",
        ),
        "inline-methodcaller": (
            "\n\nimport operator\n"
            "\n\ndef _reaches_through_an_inline_methodcaller(account):\n"
            '    """Reaches the glob through a methodcaller it never binds."""\n'
            '    return sorted(operator.methodcaller("glob", "*.sav")(account))\n',
            "_reaches_through_an_inline_methodcaller",
        ),
        "getattr-through-a-module-constant": (
            '\n\n_PRIMITIVE_NAME = "glob"\n'
            "\n\ndef _reaches_through_a_named_constant(account):\n"
            '    """Resolves the glob through getattr and a module constant."""\n'
            '    return sorted(getattr(account, _PRIMITIVE_NAME)("*.sav"))\n',
            "_reaches_through_a_named_constant",
        ),
        "def-under-a-platform-gate": (
            "\n\nimport sys\n"
            '\nif sys.platform == "win32":\n'
            "\n    def _reaches_under_a_platform_gate():\n"
            '        """The ordinary platform-fallback idiom."""\n'
            "        root = locate.resolve_save_root()\n"
            "        return locate.resolve_account_dir(root)\n",
            "_reaches_under_a_platform_gate",
        ),
        "def-under-an-import-gate": (
            "\n\ntry:\n    import functools\nexcept ImportError:\n"
            "    functools = None\nelse:\n"
            "\n    def _reaches_under_an_import_gate():\n"
            '        """The ordinary optional-dependency idiom."""\n'
            "        root = locate.resolve_save_root()\n"
            "        return locate.resolve_account_dir(root)\n",
            "_reaches_under_an_import_gate",
        ),
        "subscript-dispatch-inline": (
            '\n\n_ROUTES = {"root": locate.resolve_save_root,'
            ' "account": locate.resolve_account_dir}\n'
            "\n\ndef _reaches_through_a_dict_subscript():\n"
            '    """Dispatches through a module-scope table of function objects."""\n'
            '    return _ROUTES["account"](_ROUTES["root"]())\n',
            "_reaches_through_a_dict_subscript",
        ),
        "subscript-index-inline": (
            "\n\n_FINDERS = (locate.resolve_save_root,)\n"
            "\n\ndef _reaches_through_an_index():\n"
            '    """Dispatches through a module-scope tuple of function objects."""\n'
            "    return _FINDERS[0]()\n",
            "_reaches_through_an_index",
        ),
        "for-loop-target": (
            "\n\n_FINDERS = (locate.resolve_save_root,)\n"
            "\n\ndef _reaches_through_a_loop_target():\n"
            '    """Binds the primitive by iterating a table of them."""\n'
            "    for finder in _FINDERS:\n"
            "        return finder()\n"
            "    return None\n",
            "_reaches_through_a_loop_target",
        ),
        "with-as-target": (
            "\n\nimport contextlib\n"
            "\n\ndef _reaches_through_a_with_target():\n"
            '    """Binds the primitive with a context manager."""\n'
            "    with contextlib.nullcontext(locate.resolve_save_root) as finder:\n"
            "        return finder()\n",
            "_reaches_through_a_with_target",
        ),
        "comprehension-target": (
            "\n\n_FINDERS = (locate.resolve_save_root,)\n"
            "\n\ndef _reaches_through_a_comprehension():\n"
            '    """Binds the primitive as a comprehension variable."""\n'
            "    return [one() for one in _FINDERS]\n",
            "_reaches_through_a_comprehension",
        ),
        "default-argument": (
            "\n\ndef _reaches_through_a_default(finder=locate.resolve_save_root):\n"
            '    """Names the primitive once, in a signature."""\n'
            "    return finder()\n",
            "_reaches_through_a_default",
        ),
        "conditional-callee": (
            "\n\nimport sys\n"
            "\n\ndef _reaches_through_a_conditional_callee():\n"
            '    """Chooses the callee with a conditional expression."""\n'
            "    return (locate.resolve_save_root if sys.platform else dict)()\n",
            "_reaches_through_a_conditional_callee",
        ),
        "fallback-callee": (
            "\n\n_OVERRIDE = None\n"
            "\n\ndef _reaches_through_a_fallback_callee():\n"
            '    """The ordinary override-with-fallback idiom."""\n'
            "    return (_OVERRIDE or locate.resolve_save_root)()\n",
            "_reaches_through_a_fallback_callee",
        ),
        "inline-partial": (
            "\n\nimport functools\n"
            "\n\ndef _reaches_through_an_inline_partial():\n"
            '    """Builds and calls the partial in one expression."""\n'
            "    return functools.partial(locate.resolve_save_root)()\n",
            "_reaches_through_an_inline_partial",
        ),
        "getattr-handed-back-uncalled": (
            '\n\n_PRIMITIVE_NAME = "glob"\n'
            "\n\ndef _hands_back_a_resolved_primitive(account):\n"
            '    """Resolves the glob through getattr and hands it back uncalled."""\n'
            "    return getattr(account, _PRIMITIVE_NAME)\n",
            "_hands_back_a_resolved_primitive",
        ),
        "function-local-alias": (
            "\n\ndef _reaches_through_a_local_alias():\n"
            '    """Binds the locator to a local and calls the local."""\n'
            "    finder = locate.resolve_save_root\n"
            "    return finder()\n",
            "_reaches_through_a_local_alias",
        ),
    }
)


def _module_scope_exemption(path: Path) -> Mapping[str, str]:
    """The sentinel declaration a planted module needs, when it needs one at all.

    THE LAMBDA ROUTE NEEDS ONE AND THE OTHERS DO NOT, and that asymmetry is a
    measurement rather than a convenience. ``ast.Lambda`` is not a function to
    :func:`_module_scope_reaches`, so a call inside a module-scope lambda body
    reads as a module-scope call. CS-491's detail block records that route as
    invisible to the guard; what was measured before this control was written is
    narrower and worse in one way - the guard SEES it, files it under
    :data:`MODULE_SCOPE_REACH`, and therefore names no function, so a module
    that legitimately declares the sentinel hides the reaching helper entirely.
    Declaring the sentinel here is what forces this control to grade the
    FUNCTION rather than settle for the sentinel's red.

    Args:
        path: The planted module's file.

    Returns:
        The sentinel exemption when the module reaches at module scope, and an
        empty mapping otherwise - an unneeded declaration is itself a red, under
        ``a declaration names a function that no longer exists``.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    primitives = _effective_primitives(tree, _LIBRARY_PRIMITIVES, source=path)
    if _module_scope_reaches(tree, primitives):
        return MappingProxyType({MODULE_SCOPE_REACH: "the planted route's own module-scope call"})
    return MappingProxyType({})


@pytest.mark.parametrize(
    ("label", "route", "reported"),
    [(label, route, reported) for label, (route, reported) in _ALIASED_REACH_ROUTES.items()],
    ids=list(_ALIASED_REACH_ROUTES),
)
def test_a_primitive_reached_through_an_alias_is_named_by_the_guard(
    tmp_path: Path, label: str, route: str, reported: str
) -> None:
    """CS-491's aliasing half, forced at the VERDICT rather than at a predicate.

    CS-471's clause 3 shipped a widening that moved no verdict on any tree, and
    the item's own fence says any CS-491 acceptance has to move one. So each
    route is planted beside a declared companion and the guard's FAILURE has to
    carry the evading function's name - not a boolean, not a predicate, and not
    the guard reddening for some unrelated reason.

    THREE THINGS ARE GRADED PER ROUTE and the third is the one CS-471 taught:

    - The guard names the evader.
    - The companion ALONE is accepted, so the red above is the route rather than
      the guard rejecting the planted shape wholesale.
    - The CLASSIFIER picks up a module whose ONLY reach is this route. Fixing a
      guard without fixing the thing that decides which files the guard runs on
      is half a fix that measures green, and that is not a hypothetical - it is
      what CS-471 shipped and a refutation pass measured.

    It needs no save library - it is a claim about the repo, not about a world.

    Args:
        tmp_path: The per-test temporary directory.
        label: The route's name, used for the planted filenames and a message.
        route: The evading source to plant beside the companion.
        reported: The name the guard's failure has to carry.
    """
    stem = label.replace("-", "_")
    planted = tmp_path / f"test_planted_{stem}.py"
    planted.write_text(_DECLARED_COMPANION + route, encoding="utf-8")

    with pytest.raises(AssertionError) as caught:
        _assert_library_reach_is_declared(
            planted, graded=_COMPANION_GRADED, exempt=_module_scope_exemption(planted)
        )
    assert reported in str(caught.value), (
        f"the guard failed on the {label} route without naming {reported}, so it "
        f"reddened for another reason and this route is still unmeasured. The "
        f"guard said: {caught.value}"
    )

    companion_only = tmp_path / f"test_companion_{stem}.py"
    companion_only.write_text(_DECLARED_COMPANION, encoding="utf-8")
    _assert_library_reach_is_declared(companion_only, graded=_COMPANION_GRADED, exempt={})

    alone = tmp_path / f"test_alone_{stem}.py"
    alone.write_text("from clockspeed.data import locate\n" + route, encoding="utf-8")
    assert _module_reaches(alone), (
        f"a module whose ONLY reach is the {label} route is classed SILENT, so "
        "the suite-wide guard never runs on it and the red above is reachable "
        "only by a caller that already suspected the module. That is the CS-471 "
        "half-fix shape exactly."
    )


#: Reach routes spelled OUTSIDE every ``def``, label to the source to plant.
#:
#: THESE ARE CS-491's TWELFTH HOLE AND THE REASON THERE WAS A ROUND THREE.
#: ``_module_scope_reaches`` re-derived the callee name itself - an ``Attribute``
#: or a bare ``Name``, the pre-CS-491 test hand-inlined - while ``_calls_any``
#: had grown five channels. So every route closed in rounds one and two reopened
#: by moving it one indentation level out of its ``def``, escaping the guard AND
#: the classifier at once. A refutation pass measured all of these; the file's
#: own ``MODULE_SCOPE_REACH`` note already said hoisting is the ordinary way to
#: build a parametrize list, "the likeliest shape to meet, not the least".
_MODULE_SCOPE_ROUTES: Final = MappingProxyType(
    {
        "subscript-dispatch": (
            '\n\n_ROUTES = {"root": locate.resolve_save_root}\n_ACCOUNT = _ROUTES["root"]()\n'
        ),
        "partial": (
            "\n\nimport functools\n_ACCOUNT = functools.partial(locate.resolve_save_root)()\n"
        ),
        "getattr-through-a-constant": (
            '\n\n_PRIMITIVE_NAME = "resolve_save_root"\n'
            "_ACCOUNT = getattr(locate, _PRIMITIVE_NAME)()\n"
        ),
        "conditional-callee": (
            "\n\nimport sys\n"
            '_ACCOUNT = (locate.resolve_save_root if sys.platform == "win32" else dict)()\n'
        ),
        "class-body": ("\n\nclass _Holder:\n    ACCOUNT = locate.resolve_save_root()\n"),
    }
)


@pytest.mark.parametrize(
    ("label", "route"),
    list(_MODULE_SCOPE_ROUTES.items()),
    ids=list(_MODULE_SCOPE_ROUTES),
)
def test_a_module_scope_reach_through_an_alias_is_reported(
    tmp_path: Path, label: str, route: str
) -> None:
    """CS-491's twelfth hole: the same routes, one indentation level out.

    A reach outside every ``def`` has no function name to report, so the verdict
    that has to move is the SENTINEL: undeclared, the guard must red naming
    :data:`MODULE_SCOPE_REACH`, and declaring it must then be accepted - which
    is what makes the red the route rather than the guard refusing the shape.

    THE CLASSIFIER IS GRADED TOO, and here it is not a formality. Each of these
    was measured with ``_module_reaches`` answering False, which means the
    suite-wide guard never ran on the module at all and no declaration anywhere
    could have helped.

    It needs no save library - it is a claim about the repo, not about a world.

    Args:
        tmp_path: The per-test temporary directory.
        label: The route's name, used for the planted filename and a message.
        route: The module-scope source to plant beside the companion.
    """
    stem = label.replace("-", "_")
    alone = tmp_path / f"test_alone_{stem}.py"
    alone.write_text("from clockspeed.data import locate\n" + route, encoding="utf-8")
    assert _module_reaches(alone), (
        f"a module whose only reach is the module-scope {label} route is classed "
        "SILENT, so the suite-wide guard never runs on it."
    )

    planted = tmp_path / f"test_planted_ms_{stem}.py"
    planted.write_text(_DECLARED_COMPANION + route, encoding="utf-8")

    with pytest.raises(AssertionError) as caught:
        _assert_library_reach_is_declared(planted, graded=_COMPANION_GRADED, exempt={})
    assert MODULE_SCOPE_REACH in str(caught.value), (
        f"the guard did not file the module-scope {label} route under the "
        f"sentinel. It said: {caught.value}"
    )

    _assert_library_reach_is_declared(
        planted,
        graded=_COMPANION_GRADED,
        exempt={MODULE_SCOPE_REACH: "the planted route's own module-scope call"},
    )


#: A planted SIBLING whose helper reaches the library and which declares it.
#: Planted rather than pointed at a tracked module, so this control states its
#: own premise instead of depending on which helpers a real sibling happens to
#: ship this week.
_REACHING_SIBLING_SOURCE: Final = '''
from types import MappingProxyType

from clockspeed.data import locate


def _sibling_sweep() -> list:
    """Reads the library and hands back its paths."""
    root = locate.resolve_save_root()
    return sorted(locate.resolve_account_dir(root).glob("*.sav"))


_GRADED_LIBRARY_REACH = MappingProxyType({"_sibling_sweep": "reads every save in the library"})
_EXEMPT_LIBRARY_REACH = MappingProxyType({})
'''

#: A module whose ONLY route into the library is that sibling's helper.
_SIBLING_IMPORT_SOURCE: Final = '''
from planted_sibling import _sibling_sweep


def _reaches_through_a_sibling():
    """Calls a sibling's declared sweep and names no primitive at all."""
    return _sibling_sweep()
'''

#: A planted sibling whose primitive-touching helper is declared EXEMPT - it
#: globs a repository directory, not a save root.
_EXEMPT_SIBLING_SOURCE: Final = '''
from pathlib import Path
from types import MappingProxyType


def _sibling_repo_glob() -> list:
    """Globs the module's own directory, which is a repo path."""
    return sorted(Path(__file__).parent.glob("*.py"))


_GRADED_LIBRARY_REACH = MappingProxyType({})
_EXEMPT_LIBRARY_REACH = MappingProxyType(
    {"_sibling_repo_glob": "globs a repo directory, never a save root"}
)
'''

#: A module calling that exempt helper. It reaches NO library and must stay
#: silent.
_EXEMPT_SIBLING_IMPORT_SOURCE: Final = '''
from planted_exempt_sibling import _sibling_repo_glob


def _lists_repo_sources():
    """Calls a sibling helper that touches a primitive and reaches no library."""
    return _sibling_repo_glob()
'''

#: The shape this package actually uses: the MODULE is imported and the helper
#: is spelled as an attribute of it. Pointed at the real ``test_properties``
#: because that is the real arrangement, and a planted stand-in would grade a
#: shape nothing ships. NO COUNT IS QUOTED. The sentence here used to say
#: "eleven tracked modules import it this way"; a refutation pass measured
#: EIGHT, and found that eleven is the number of modules the classifier calls
#: reaching - a real measurement of a different thing. A measured number in
#: prose is what CLAUDE.md section 4 forbids, for this reason exactly.
_SIBLING_MODULE_HANDLE_SOURCE: Final = '''
from tests.save import test_properties


def _reaches_through_a_module_handle():
    """Calls a sibling's declared sweep through the imported module object."""
    return test_properties._sweep_payload_tags()
'''


def test_a_module_reaching_only_through_a_sibling_helper_is_not_classed_silent(
    tmp_path: Path,
) -> None:
    """CS-491's CROSS-MODULE route, which needed the classifier and not the guard.

    A module with no primitive call of its own was classed SILENT, so the
    suite-wide guard never ran on it - the reach was invisible twice over, the
    same shape as CS-471's module-scope hole and for the same reason.

    BOTH HALVES ARE GRADED. The classifier has to pick the module up, and the
    guard then has to name the function. Either alone is the half-fix.

    It needs no save library - it is a claim about the repo, not about a world.
    """
    (tmp_path / "planted_sibling.py").write_text(_REACHING_SIBLING_SOURCE, encoding="utf-8")
    planted = tmp_path / "test_planted_sibling_import.py"
    planted.write_text(_SIBLING_IMPORT_SOURCE, encoding="utf-8")

    assert _module_reaches(planted), (
        "a module whose only route into the library is a sibling's declared "
        "sweep is still classed SILENT, so the suite-wide guard never runs on "
        "it and nothing downstream can report it."
    )

    with pytest.raises(AssertionError) as caught:
        _assert_library_reach_is_declared(planted, graded={}, exempt={})
    assert "_reaches_through_a_sibling" in str(caught.value), (
        f"the guard did not name the function calling the sibling's sweep. It said: {caught.value}"
    )


def test_the_module_handle_shape_this_package_actually_uses_is_resolved(
    tmp_path: Path,
) -> None:
    """The cross-module route in the spelling eleven tracked modules use.

    ``from tests.save import test_properties`` binds the MODULE, after which the
    sweep is spelled as an attribute of it. Resolving only ``from
    tests.save.test_properties import _sweep_payload_tags`` would close the
    shape nothing ships and leave the shape everything ships open, which is the
    CS-477 pattern - a repair that moves the seam up one level.

    It needs no save library - it is a claim about the repo, not about a world.
    """
    planted = tmp_path / "test_planted_module_handle.py"
    planted.write_text(_SIBLING_MODULE_HANDLE_SOURCE, encoding="utf-8")

    assert _module_reaches(planted), (
        "a module calling this module's own declared sweep through an imported "
        "module object is classed SILENT, so the guard never runs on it."
    )

    with pytest.raises(AssertionError) as caught:
        _assert_library_reach_is_declared(planted, graded={}, exempt={})
    assert "_reaches_through_a_module_handle" in str(caught.value), (
        f"the guard did not name the function reaching through the module "
        f"handle. It said: {caught.value}"
    )


def test_a_siblings_exempt_helper_does_not_export_a_reach_it_does_not_have(
    tmp_path: Path,
) -> None:
    """THE NEGATIVE HALF, and it is load-bearing rather than symmetric decoration.

    Touching a primitive is not reaching the library - that distinction is the
    whole purpose of ``_EXEMPT_LIBRARY_REACH``. The FIRST DRAFT of the sibling
    resolution exported every directly reaching function, and it was measured on
    the shipped tree: ``test_absolute_claims`` imports
    ``test_oracle_citations``, whose ``_sources_under`` globs THIS REPOSITORY,
    and seven functions in that module were required to declare a library reach
    none of them has. Seven reasons describing something the code does not do is
    the defect CS-471 shipped eight of, generated automatically.

    A CONTROL WHOSE STUB SATISFIES EVERY INPUT IS A TAUTOLOGY, so this asserts
    the reaching sibling one function up is picked up. Without that half, a
    resolution that exported NOTHING would satisfy this test.

    It needs no save library - it is a claim about the repo, not about a world.
    """
    (tmp_path / "planted_exempt_sibling.py").write_text(_EXEMPT_SIBLING_SOURCE, encoding="utf-8")
    planted = tmp_path / "test_planted_exempt_import.py"
    planted.write_text(_EXEMPT_SIBLING_IMPORT_SOURCE, encoding="utf-8")

    assert not _module_reaches(planted), (
        "calling a sibling helper that the sibling itself declares EXEMPT - it "
        "globs a repo directory - was reported as reaching the save library. "
        "That puts a false reason on every caller."
    )

    (tmp_path / "planted_sibling.py").write_text(_REACHING_SIBLING_SOURCE, encoding="utf-8")
    reaching = tmp_path / "test_planted_reaching_import.py"
    reaching.write_text(_SIBLING_IMPORT_SOURCE, encoding="utf-8")
    assert _module_reaches(reaching), (
        "the sibling resolution reports nothing for a GRADED sibling helper "
        "either, so the silence above is the resolution being switched off "
        "rather than it discriminating."
    )


#: A sibling whose GRADED helper reaches the library only through ANOTHER of its
#: graded helpers. It calls no primitive of its own.
_INDIRECT_SIBLING_SOURCE: Final = '''
from pathlib import Path
from types import MappingProxyType

from clockspeed.data import locate


def _sibling_reads() -> Path:
    """Reaches the library directly."""
    root = locate.resolve_save_root()
    return locate.resolve_account_dir(root)


def _sibling_hands_it_on() -> Path:
    """Takes the account directory from the helper above and passes it along."""
    return _sibling_reads()


_GRADED_LIBRARY_REACH = MappingProxyType(
    {
        "_sibling_reads": "reads the library",
        "_sibling_hands_it_on": "takes the account directory from _sibling_reads",
    }
)
_EXEMPT_LIBRARY_REACH = MappingProxyType({})
'''

#: Spellings of the cross-module route, label to the importing module's source
#: and the function the guard has to name. The first two are import STATEMENTS;
#: the third names the sibling as a runtime string, which no import statement
#: resolves.
_SIBLING_SPELLINGS: Final = MappingProxyType(
    {
        "star-import": (
            "from planted_sibling import *\n"
            "\n\ndef _reaches_through_a_star_import():\n"
            '    """Takes the sibling\'s whole namespace and calls its sweep."""\n'
            "    return _sibling_sweep()\n",
            "_reaches_through_a_star_import",
        ),
        "importlib-handle": (
            "import importlib\n"
            '\n_sib = importlib.import_module("planted_sibling")\n'
            "\n\ndef _reaches_through_importlib():\n"
            '    """Takes the sibling module object at runtime rather than by syntax."""\n'
            "    return _sib._sibling_sweep()\n",
            "_reaches_through_importlib",
        ),
    }
)


@pytest.mark.parametrize(
    ("label", "importing", "reported"),
    [(label, importing, reported) for label, (importing, reported) in _SIBLING_SPELLINGS.items()],
    ids=list(_SIBLING_SPELLINGS),
)
def test_every_spelling_of_the_cross_module_route_is_resolved(
    tmp_path: Path, label: str, importing: str, reported: str
) -> None:
    """The sibling route spelled without an import STATEMENT naming the helper.

    Round one resolved ``from pkg.mod import helper`` and ``from pkg import
    mod``, and a refutation pass measured both of these past it. A star import
    binds the sibling's whole namespace, so the helper arrives under the
    sibling's own name and no ``alias.name`` matches it.
    ``importlib.import_module`` names the sibling as a STRING, so there is no
    import statement to read at all - and this module spells it that way itself.

    Resolving only the spellings that happen to be readable is the CS-477
    pattern: a repair that moves the seam up one level rather than removing it.

    It needs no save library - it is a claim about the repo, not about a world.

    Args:
        tmp_path: The per-test temporary directory.
        label: The spelling's name, used for the planted filename and a message.
        importing: The importing module's source.
        reported: The name the guard's failure has to carry.
    """
    (tmp_path / "planted_sibling.py").write_text(_REACHING_SIBLING_SOURCE, encoding="utf-8")
    planted = tmp_path / f"test_planted_{label.replace('-', '_')}.py"
    planted.write_text(importing, encoding="utf-8")

    assert _module_reaches(planted), (
        f"a module reaching a sibling's declared sweep through a {label} is classed "
        "SILENT, so the suite-wide guard never runs on it."
    )

    with pytest.raises(AssertionError) as caught:
        _assert_library_reach_is_declared(planted, graded={}, exempt={})
    assert reported in str(caught.value), (
        f"the guard did not name the function reaching through the {label}. It said: {caught.value}"
    )


def test_a_siblings_graded_helper_that_reaches_indirectly_is_still_exported(
    tmp_path: Path,
) -> None:
    """The cross-module export keyed on the DIRECT set alone missed a graded helper.

    A helper that takes its body or its path from another graded helper calls no
    primitive itself, so it was not in the sibling's direct set, so it was not
    exported, so a module importing and calling it was still classed silent. The
    export now mirrors the guard - ``graded & (direct | indirect)`` - rather than
    approximating it.

    THE PRIVACY REFUTATION PASS FOUND THIS OUTSIDE ITS OWN LENS and said so
    rather than letting it go, which is why it is closed here instead of being
    filed.

    It needs no save library - it is a claim about the repo, not about a world.
    """
    (tmp_path / "planted_sibling.py").write_text(_INDIRECT_SIBLING_SOURCE, encoding="utf-8")
    planted = tmp_path / "test_planted_indirect_sibling.py"
    planted.write_text(
        "from planted_sibling import _sibling_hands_it_on\n"
        "\n\ndef _reaches_through_an_indirect_helper():\n"
        '    """Calls a graded helper that reaches only through another one."""\n'
        "    return _sibling_hands_it_on()\n",
        encoding="utf-8",
    )

    assert _module_reaches(planted), (
        "a module calling a sibling's GRADED helper is classed SILENT because that "
        "helper reaches through another helper rather than through a primitive of "
        "its own. The guard never runs on it."
    )

    with pytest.raises(AssertionError) as caught:
        _assert_library_reach_is_declared(planted, graded={}, exempt={})
    assert "_reaches_through_an_indirect_helper" in str(caught.value), (
        f"the guard did not name the caller. It said: {caught.value}"
    )


def test_the_guards_failure_message_names_functions_and_never_a_path(
    tmp_path: Path,
) -> None:
    """NON-NEGOTIABLE 12, ENFORCED rather than left as a property of today's strings.

    A refutation pass on this work counted the renderings of a caught exception
    into an f-string in this module rising from nine to nineteen, and pointed out
    that ``tests/test_exception_rendering.py`` keys on an AST shape inside an
    ``except`` handler - so ``with pytest.raises(...) as caught`` followed by
    ``f"{caught.value}"`` is structurally invisible to it. All of them are safe
    only because :func:`_assert_library_reach_is_declared` formats sorted lists
    of FUNCTION NAMES and nothing else. That was a property of one function's
    message strings that no test held. This holds it: add the module path to any
    of those messages and this goes red before the echo ships.

    THE PLANTED MODULE'S PATH IS THE ADVERSARY. It sits under ``tmp_path``, whose
    real prefix on this machine carries the Windows account name, so a message
    that interpolated it would fail here for the same reason a save path would.

    It needs no save library - it is a claim about the repo, not about a world.
    """
    planted = tmp_path / "test_planted_message_hygiene.py"
    planted.write_text(_UNDECLARED_MODULE_SOURCE, encoding="utf-8")

    with pytest.raises(AssertionError) as caught:
        _assert_library_reach_is_declared(planted, graded={}, exempt={})
    message = str(caught.value)

    assert "_helper_that_reaches" in message, (
        "the guard did not name the reaching function, so the message this test "
        f"is scanning is not the one the guard reports: {message}"
    )
    for forbidden in (str(planted), str(tmp_path), planted.name, "/", "\\"):
        assert forbidden not in message, (
            f"the guard's failure message carries {forbidden!r}. A path rendered "
            "out of this guard reaches every one of the nineteen f-strings in this "
            "module that interpolate a caught AssertionError, and non-negotiable 12 "
            f"counts an error message as an echo path. The message was: {message}"
        )


#: Wrapper defeats, label to the class source that holds the body and the return
#: annotation the reaching helper carries.
#:
#: EVERY ONE WAS MEASURED NOT FLAGGED, by a refutation pass with a proof of
#: concept run on a machine with no game. The first four were measured after
#: CS-471 closed; the last four were measured after CS-491's FIRST round closed,
#: by a pass that refuted it, and they are the reason there was a second round.
_WRAPPER_DEFEATS: Final = MappingProxyType(
    {
        "bytearray-field": (
            "@dataclass(frozen=True)\nclass _Wrapped:\n    body: bytearray\n",
            "_Wrapped",
        ),
        "memoryview-field": (
            "@dataclass(frozen=True)\nclass _Wrapped:\n    body: memoryview\n",
            "_Wrapped",
        ),
        "bytesio-field": (
            "@dataclass(frozen=True)\nclass _Wrapped:\n    body: BytesIO\n",
            "_Wrapped",
        ),
        "unannotated-attribute": (
            "class _Wrapped:\n"
            "    def __init__(self, body: bytes) -> None:\n"
            "        self.body = body\n",
            "_Wrapped",
        ),
        "type-alias-assignment": (
            "_Body = bytes\n\n\n@dataclass(frozen=True)\nclass _Wrapped:\n    body: _Body\n",
            "_Wrapped",
        ),
        "type-alias-statement": (
            "type _Body = bytes\n\n\n@dataclass(frozen=True)\nclass _Wrapped:\n    body: _Body\n",
            "_Wrapped",
        ),
        "property-accessor": (
            "class _Wrapped:\n"
            "    def __init__(self, raw: object) -> None:\n"
            "        self._held = raw\n"
            "\n"
            "    @property\n"
            "    def body(self) -> bytes:\n"
            "        return bytes(self._held)\n",
            "_Wrapped",
        ),
        "annotated-store-only": (
            "class _Wrapped:\n"
            "    def __init__(self, raw: object) -> None:\n"
            "        self.body: bytes = bytes(raw)\n",
            "_Wrapped",
        ),
        "widening-store-annotation": (
            "class _Wrapped:\n"
            "    def __init__(self, body: bytes) -> None:\n"
            "        self.body: object = body\n",
            "_Wrapped",
        ),
        "tuple-target-store": (
            "class _Wrapped:\n"
            "    def __init__(self, body: bytes, count: int) -> None:\n"
            "        self.body, self.count = body, count\n",
            "_Wrapped",
        ),
        "wrapper-class-alias": (
            "@dataclass(frozen=True)\nclass _Wrapped:\n    body: bytes\n\n\n_Alias = _Wrapped\n",
            "_Alias",
        ),
    }
)

#: The module a wrapper defeat is planted into. The helper REACHES and hands the
#: wrapper back; its CALLER is the function whose verdict has to move.
_WRAPPER_MODULE_TEMPLATE: Final = '''
from dataclasses import dataclass
from io import BytesIO

from clockspeed.data import locate

{wrapper}

def _reaches_and_wraps() -> {annotation}:
    """Reaches the library and hands its caller the body inside a wrapper."""
    root = locate.resolve_save_root()
    account = locate.resolve_account_dir(root)
    return _Wrapped(sorted(account.glob("*.sav"))[0].read_bytes())


def _takes_the_wrapper():
    """Takes the whole decompressed world and declares nothing."""
    return _reaches_and_wraps()
'''


@pytest.mark.parametrize("label", list(_WRAPPER_DEFEATS), ids=list(_WRAPPER_DEFEATS))
def test_a_wrapper_holding_the_body_in_another_shape_is_flagged_as_propagating(
    tmp_path: Path, label: str
) -> None:
    """CS-491's wrapper half - every shape measured past a narrower rule.

    ``_body_wrapping_classes`` compared the rendered field annotation against
    the words ``bytes`` and ``Path``, so a field typed ``bytearray``,
    ``memoryview`` or ``BytesIO`` held the same decompressed world and read as a
    scalar; and an attribute bound in ``__init__`` without an annotation read as
    nothing at all.

    FOUR MORE SHAPES CAME FROM THE PASS THAT REFUTED ROUND ONE, and each is
    ordinary rather than adversarial. A type alias for the body type - three
    spellings - switched the walk off entirely, because an alias for a PRIMITIVE
    was resolved to a fixpoint and an alias for a TYPE was not. A store
    annotated ``object`` laundered the parameter's own annotation. A tuple
    target could not be paired with its value. And an alias for the WRAPPER
    CLASS defeated the consequence while the walk still found the class.

    BOTH RULES ARE RUN ON THE SAME NODE, which is what makes this a measurement
    of the widening rather than a restatement of it, and THE CONSEQUENCE IS
    GRADED TOO - the caller has to be reported as an undeclared indirect reach
    site. Checking the boolean alone is the half that would leave CS-471's
    clause 3 inert all over again.

    It needs no save library - it is a claim about the repo, not about a world.

    Args:
        tmp_path: The per-test temporary directory.
        label: The defeat's name, used for the planted filename and a message.
    """
    wrapper, annotation = _WRAPPER_DEFEATS[label]
    planted = tmp_path / f"test_planted_{label.replace('-', '_')}.py"
    planted.write_text(
        _WRAPPER_MODULE_TEMPLATE.format(wrapper=wrapper, annotation=annotation), encoding="utf-8"
    )
    tree = ast.parse(planted.read_text(encoding="utf-8"))
    functions = _scanned_functions(tree)

    personal = _personal_data_names(tree, source=planted)
    assert annotation in personal, (
        f"the annotation {annotation} of a helper handing back a {label} wrapper is "
        f"not in the personal-data name set {sorted(personal)}. The verdict below "
        "would then be measuring something other than this shape."
    )

    node = functions["_reaches_and_wraps"]
    assert not _returns_personal_data(node), (
        f"the OLD rule already called a {label} wrapper personal, so this control "
        "grades nothing and there was no defect to close here."
    )
    assert _returns_personal_data(node, personal), (
        f"the widened rule still calls a helper returning a {label} wrapper "
        "clean, which is the evasion this control exists for."
    )

    with pytest.raises(AssertionError) as caught:
        _assert_library_reach_is_declared(
            planted,
            graded={"_reaches_and_wraps": "reaches and hands back a wrapped body"},
            exempt={},
        )
    assert "_takes_the_wrapper" in str(caught.value), (
        "the caller of the wrapper-returning helper was not reported as an "
        f"undeclared indirect reach site. The guard said: {caught.value}"
    )


#: A sibling that defines the wrapper, and the module that imports it. The
#: fixed point took the module's OWN classes, so a class imported from a sibling
#: was outside it - measured, and the last of CS-491's wrapper defeats.
_WRAPPER_SIBLING_SOURCE: Final = """
from dataclasses import dataclass


@dataclass(frozen=True)
class Wrapped:
    body: bytes
"""

_WRAPPER_IMPORT_SOURCE: Final = '''
from clockspeed.data import locate
from planted_wrapper_sibling import Wrapped


def _reaches_and_wraps() -> Wrapped:
    """Reaches the library and wraps the body in a class from a sibling."""
    root = locate.resolve_save_root()
    account = locate.resolve_account_dir(root)
    return Wrapped(sorted(account.glob("*.sav"))[0].read_bytes())


def _takes_the_wrapper():
    """Takes the whole decompressed world and declares nothing."""
    return _reaches_and_wraps()
'''


def test_a_wrapper_class_imported_from_a_sibling_is_resolved(tmp_path: Path) -> None:
    """The wrapper fixed point reached the module's own classes and stopped there.

    A class imported from a sibling was outside it, so the same dataclass
    propagated or did not depending on which file it was written in. Graded at
    the verdict, like the defeats above.

    It needs no save library - it is a claim about the repo, not about a world.
    """
    (tmp_path / "planted_wrapper_sibling.py").write_text(_WRAPPER_SIBLING_SOURCE, encoding="utf-8")
    planted = tmp_path / "test_planted_wrapper_import.py"
    planted.write_text(_WRAPPER_IMPORT_SOURCE, encoding="utf-8")

    wrapping = _body_wrapping_classes(ast.parse(_WRAPPER_IMPORT_SOURCE), source=planted)
    assert "Wrapped" in wrapping, (
        f"a wrapper class imported from a sibling was not resolved: {sorted(wrapping)}"
    )

    with pytest.raises(AssertionError) as caught:
        _assert_library_reach_is_declared(
            planted,
            graded={"_reaches_and_wraps": "reaches and hands back a sibling's wrapper"},
            exempt={},
        )
    assert "_takes_the_wrapper" in str(caught.value), (
        f"the caller was not reported as an undeclared indirect reach site. The "
        f"guard said: {caught.value}"
    )


#: The same sibling wrapper, reached through the MODULE rather than by name.
_WRAPPER_HANDLE_SOURCE: Final = '''
import planted_wrapper_sibling
from clockspeed.data import locate


def _reaches_and_wraps() -> planted_wrapper_sibling.Wrapped:
    """Reaches the library and annotates the wrapper through the module handle."""
    root = locate.resolve_save_root()
    account = locate.resolve_account_dir(root)
    return planted_wrapper_sibling.Wrapped(sorted(account.glob("*.sav"))[0].read_bytes())


def _takes_the_wrapper():
    """Takes the whole decompressed world and declares nothing."""
    return _reaches_and_wraps()
'''


def test_a_wrapper_class_annotated_through_a_module_handle_is_resolved(
    tmp_path: Path,
) -> None:
    """The wrapper half resolved one import spelling while the reach half resolved two.

    ``from pkg.mod import Wrapped`` was resolved; ``import mod`` followed by an
    annotation spelled ``mod.Wrapped`` was not - the same mechanism applied to
    one of two populations, which is the shape this whole item kept turning up.
    Graded at the verdict, like every other defeat here.

    It needs no save library - it is a claim about the repo, not about a world.
    """
    (tmp_path / "planted_wrapper_sibling.py").write_text(_WRAPPER_SIBLING_SOURCE, encoding="utf-8")
    planted = tmp_path / "test_planted_wrapper_handle.py"
    planted.write_text(_WRAPPER_HANDLE_SOURCE, encoding="utf-8")

    personal = _personal_data_names(ast.parse(_WRAPPER_HANDLE_SOURCE), source=planted)
    assert "Wrapped" in personal, (
        f"a wrapper class annotated through a module handle was not resolved: {sorted(personal)}"
    )

    with pytest.raises(AssertionError) as caught:
        _assert_library_reach_is_declared(
            planted,
            graded={"_reaches_and_wraps": "reaches and hands back a sibling's wrapper"},
            exempt={},
        )
    assert "_takes_the_wrapper" in str(caught.value), (
        f"the caller was not reported as an undeclared indirect reach site. The "
        f"guard said: {caught.value}"
    )


#: A primitive named as a STRING in order to REPLACE it, which is the opposite
#: of a reach site.
_NAMED_TO_BE_BROKEN_SOURCE: Final = '''

def _raise(*_args, **_kwargs):
    """Stand in for a primitive and fail."""
    raise OSError


def test_the_locator_failure_is_contained(monkeypatch):
    """Names two primitives as strings in order to break them."""
    monkeypatch.setattr(locate, "resolve_save_root", _raise)
    monkeypatch.setattr(locate, "glob", _raise)
'''

#: A module-scope vocabulary of primitive NAMES, held in a tuple and a dict.
#: This module ships several, and so does every consuming module - the reach
#: declarations themselves are dicts keyed by function name.
_VOCABULARY_CONSTANT_SOURCE: Final = '''

_NAMES = ("glob", "read_bytes", "resolve_save_root")
_REASONS = {"glob": "why it is in the set", "iterdir": "why it is in the set"}


def _reads_the_vocabulary():
    """Reads two constants that NAME primitives and touches no filesystem."""
    return sorted(_NAMES) + sorted(_REASONS)
'''


@pytest.mark.parametrize(
    ("label", "innocent"),
    [
        ("named-only-to-be-broken", _NAMED_TO_BE_BROKEN_SOURCE),
        ("vocabulary-constant", _VOCABULARY_CONSTANT_SOURCE),
    ],
    ids=["named-only-to-be-broken", "vocabulary-constant"],
)
def test_the_widening_does_not_flag_a_module_that_only_names_a_primitive(
    tmp_path: Path, label: str, innocent: str
) -> None:
    """THE INVERSION, HELD ACROSS CS-491's WIDENING. Both halves were at risk.

    ``monkeypatch.setattr(locate, "resolve_save_root", _raise)`` names a
    primitive as a string in order to BREAK it, and CS-491 added two ways to
    resolve a primitive FROM a string. Flagging those graders is the inversion
    this guard's keying note records, and it would put a library-reach
    declaration on every forced-failure test in the package.

    THE VOCABULARY HALF IS THE SAME RISK IN THIS MODULE'S OWN SHAPE. A primitive
    name inside a tuple or a dict literal must not bind an alias, or every reach
    declaration in this package - they are dicts keyed by function name - and
    every primitive constant resolves to a primitive and the guard flags
    everything. That bound is stated in :func:`_resolves_by_string` and this is
    what holds it.

    The companion is present so the guard is not vacuous, and it is the ONLY
    function either verdict may name.

    It needs no save library - it is a claim about the repo, not about a world.

    Args:
        tmp_path: The per-test temporary directory.
        label: The shape's name, used for the planted filename and a message.
        innocent: The source that names a primitive without reaching one.
    """
    planted = tmp_path / f"test_planted_{label.replace('-', '_')}.py"
    planted.write_text(_DECLARED_COMPANION + innocent, encoding="utf-8")

    _assert_library_reach_is_declared(planted, graded=_COMPANION_GRADED, exempt={})


#: The words :data:`_PERSONAL_DATA_TYPES` must not lose, spelled a SECOND time
#: on purpose. Every one was a measured wrapper defeat, and a pin that reads the
#: list it pins is not a pin - a refutation pass dropped ``memoryview`` from the
#: vocabulary and its parallel entry from the defeat matrix together, and the
#: suite stayed green one test lower with that defeat reopened. Nothing derives
#: this set, so the drift has to be deliberate rather than silent.
_REQUIRED_PERSONAL_DATA_WORDS: Final = frozenset(
    {"bytes", "bytearray", "memoryview", "BytesIO", "Path"}
)


def test_a_primitive_name_inside_a_collection_literal_binds_no_alias() -> None:
    """THE BOUND :func:`_resolves_by_string` STATES, asserted of the predicate itself.

    The parametrized control below claimed to hold this, and a refutation pass
    measured it INERT: widening ``_resolves_by_string`` to WALK each argument
    rather than read it directly left the entire suite green, so the sentence
    saying that control held this bound was false. A bound on one predicate is
    asserted of that predicate.

    WHAT THE WIDENING ACTUALLY COSTS, since the false sentence also overstated
    that. It does NOT make the guard "flag everything": measured, it adds a
    handful of module constants to the alias set and leaves the flagged
    FUNCTION set identical. THE COUNT THAT USED TO BE HERE WAS FIVE, ALL OF
    THEM ``test_properties``'; CS-495 split the vocabulary constants into
    ``reach_guard`` and left the declaration maps behind, so it is now spread
    over two modules. The count is dropped rather than restated because
    CLAUDE.md section 4 forbids a measured number in prose and the relocation
    is exactly how one goes stale. What it does is make every reach DECLARATION
    in this package - each a dict keyed by function name - resolve to a
    primitive, which is a lie waiting for its first caller.

    It needs no save library - it is a claim about the repo, not about a world.
    """
    # THE CALL-WRAPPED FORMS ARE THE ONES THAT MATTER, and a first draft of this
    # control tested only the bare literals - which are not Call nodes, so they
    # never reach ``_resolves_by_string`` and the widening it bounds could not
    # have flagged them either way. The mutant survived, which is how that was
    # found. Every real declaration in this package is a collection handed to
    # ``frozenset`` or ``MappingProxyType``, so those are what this asserts.
    for literal in (
        '("glob", "read_bytes")',
        '{"glob": "why it is in the set"}',
        'frozenset(("glob", "read_bytes"))',
        'MappingProxyType({"glob": "why it is in the set"})',
    ):
        statement = ast.parse(f"_NAMES = {literal}").body[0]
        assert isinstance(statement, ast.Assign)
        value = statement.value
        assert not _stands_for_a_primitive(value, _LIBRARY_PRIMITIVES), (
            f"a primitive name inside {literal} bound an alias. Every reach "
            "declaration in this package is a collection of function names, and "
            "the vocabulary constants are collections of primitive names - so "
            "this direction makes them all resolve to a primitive."
        )

    bound = ast.parse('_G = operator.methodcaller("glob", "*.sav")').body[0]
    assert isinstance(bound, ast.Assign)
    direct = bound.value
    assert _stands_for_a_primitive(direct, _LIBRARY_PRIMITIVES), (
        "a primitive named as a DIRECT argument no longer resolves, so the "
        "refusal above is the predicate being off rather than the bound holding"
    )


def test_the_personal_data_vocabulary_is_not_vacuous() -> None:
    """Every word this guard calls personal data carries a reason, and matches.

    BOTH DIRECTIONS, because a vocabulary that matched everything and one that
    matched nothing would each satisfy a one-sided assertion. A stub predicate
    answering True for any annotation is the tautology CS-471's clause-2 control
    shipped, and it reported every input undeclared.

    It needs no save library - it is a claim about the repo, not about a world.
    """
    assert _PERSONAL_DATA_TYPES, "the personal-data vocabulary is empty, so the walk is vacuous"

    # THE PIN, SPELLED A SECOND TIME ON PURPOSE. A pin that reads the list it
    # pins is not a pin: a refutation pass dropped ``memoryview`` from the
    # vocabulary AND its parallel entry from the defeat matrix and the whole
    # suite stayed green, one test count lower - CS-491's own wrapper defeat
    # number two, reopened in silence. Nothing derives this set, so it is
    # written out here and the drift has to be deliberate.
    assert frozenset(_PERSONAL_DATA_TYPES) >= _REQUIRED_PERSONAL_DATA_WORDS, (
        f"the personal-data vocabulary has lost "
        f"{sorted(_REQUIRED_PERSONAL_DATA_WORDS - frozenset(_PERSONAL_DATA_TYPES))}. Each of "
        "those was a MEASURED wrapper defeat; dropping one reopens it and costs "
        "one test from the count and nothing else."
    )

    # THE POSITIVE HALF, DERIVED RATHER THAN ASSERTED OF ITSELF. The sentence
    # that stood here claimed both directions were held, and the check was
    # ``_carries_personal_data(f"{word} | None")`` - which reduces to ``word in
    # word + " | None"`` and is true for any string whatever, including a
    # vocabulary naming nothing personal at all. Measured false. What holds now
    # is that a class holding a field of that type is actually WALKED as a
    # wrapper, which no stub vocabulary satisfies.
    for word, reason in _PERSONAL_DATA_TYPES.items():
        assert reason.strip(), f"{word} is called personal data with no reason"
        held = _body_wrapping_classes(ast.parse(f"class _W:\n    body: {word}\n"))
        assert held == frozenset({"_W"}), (
            f"a class holding a field typed {word} is not walked as a wrapper, so "
            f"{word} sits in the vocabulary and changes no verdict anywhere"
        )

    for scalar in ("int", "Mapping[str, int]", "_TagSweep", "float | None"):
        assert not _carries_personal_data(scalar), (
            f"{scalar} carries nothing personal and the predicate matched it, so "
            "the widened rule matches everything and grades nothing"
        )

    # THE OVER-REACH DIRECTION, which a substring match got wrong. ``PurePosixPath``
    # and ``os.PathLike`` both contain ``Path`` and neither carries a save path,
    # and ``os.PathLike`` is written inside the guarded package.
    for lookalike in ("PurePosixPath", "os.PathLike", "PathLike | None"):
        assert not _carries_personal_data(lookalike), (
            f"{lookalike} matched the personal-data vocabulary. The reason recorded "
            "for Path is that it carries the platform account id, which is false of "
            "these - so a graded helper returning one would taint every caller with "
            "a reason describing something the code does not do"
        )


def test_no_test_in_this_module_is_gutted_to_an_early_return() -> None:
    """CS-433 - the guard against the cheapest way to fake a green suite.

    ADDED BY CS-495 RATHER THAN MOVED WITH THE CONTROLS. The five controls below
    came from ``test_properties``, which carries this check; this module did not,
    so the relocation would have moved five tests out from under it. The control
    that follows does end by running the same guard over ``__file__``, so the
    property was covered incidentally the moment the move landed - and a property
    held by whichever assertion happens to run last is the arrangement this
    package has already paid for. It is named here instead.
    """
    _assert_no_test_is_gutted(Path(__file__))


def test_the_gutting_guard_catches_a_spliced_early_return(tmp_path: Path) -> None:
    """THE GUARD'S POWER, forced rather than asserted about.

    A guard that returned an empty list on everything would pass on every module
    and read exactly like this one. The splice is the gutting shape itself,
    written against a COPY in ``tmp_path``.
    """
    spliced = tmp_path / "gutted.py"
    spliced.write_text(
        Path(__file__).read_text(encoding="utf-8") + "\n\ndef test_spliced_gutted_case():\n"
        '    """A test emptied to an early return."""\n'
        "    return\n"
        "    assert False\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError) as caught:
        _assert_no_test_is_gutted(spliced)
    assert "test_spliced_gutted_case" in str(caught.value)

    # The positive control: the unspliced source passes, so the red above is
    # the splice rather than a guard that rejects every module.
    _assert_no_test_is_gutted(Path(__file__))


def test_a_vocabulary_name_classified_nowhere_is_not_silently_a_reach_primitive() -> None:
    """CS-497 - an unclassified name must be REJECTED, not absorbed.

    WHAT WAS WRONG, MEASURED. The reach set was derived as the locators unioned
    with the vocabulary MINUS the exclusions, so a name added to
    :data:`~tests.save.reach_guard._FILESYSTEM_PRIMITIVES` and classified
    nowhere became a reach primitive by arithmetic. The partition test beside
    this one asserted ``(vocabulary - excluded) <= reach set``, which under that
    derivation reduces to ``A <= B | A`` and holds for any vocabulary whatever.
    ``fchmod`` added to the vocabulary and classified nowhere left the whole
    suite green except for two ``test_workdir`` tests that have nothing to do
    with the partition - a red for the wrong reason, which is not this property
    being graded.

    SO THE DERIVATION IS ASKED ABOUT A VOCABULARY IT HAS NOT SEEN. Asked only
    about the shipped constant, a derivation that absorbs an unclassified name
    and one that rejects it give the same answer, and no assertion over the
    shipped constant alone can separate them.

    THE INVENTED NAME IS ASSERTED ABSENT FIRST. If it ever became real
    vocabulary this control would silently start grading nothing, which is the
    shape it exists to catch.

    It needs no save library - it is a claim about the repo, not about a world.
    """
    invented = "fchmod"
    assert invented not in _FILESYSTEM_PRIMITIVES, (
        f"{invented} is real vocabulary now, so this control no longer plants an "
        "unclassified name and grades nothing. Pick a name the module does not use."
    )
    assert invented not in _NOT_LIBRARY_REACH, f"{invented} is classified as an exclusion"

    widened = frozenset(_FILESYSTEM_PRIMITIVES) | {invented}

    assert invented not in _reach_primitives(widened), (
        f"{invented} was classified nowhere and the derivation made it a reach "
        "primitive anyway. A name can be excluded with a reason, or included with "
        "one, and forgetting it must not silently pick the first thing that falls "
        "out of a set subtraction."
    )

    # NON-VACUITY, so the refusal above is the classification and not a
    # derivation that refuses everything: a name the module DOES classify as
    # reaching still comes back.
    assert "glob" in _reach_primitives(widened), (
        "a classified reach primitive dropped out of the derivation, so the "
        "refusal above says nothing about classification"
    )


def test_the_reach_primitives_partition_the_filesystem_vocabulary() -> None:
    """CS-433 - the two primitive lists are ONE list, and the split is declared.

    A HAND-MAINTAINED LIST IS THE THING THAT ROTS, and this package has watched
    it happen: the reach guard and the save-module grade each carried their own
    tuple of filesystem names, and the commit that enumerated the path-bearing
    ones for the grade left the guard naming none of them. Neither list was
    wrong at the moment it was written and they had drifted apart by the time
    anyone read both.

    So the vocabulary has one owner and the reach set is DERIVED from it by a
    partition that must be total.

    THE INCLUSION ASSERTION HERE WAS A TAUTOLOGY UNTIL CS-497, and the record of
    that stays because the shape is worth recognising again. The docstring used
    to say that adding a name to
    :data:`~tests.save.reach_guard._FILESYSTEM_PRIMITIVES` either makes it a
    reach primitive or requires a written reason it is not, "and there is no
    third outcome that leaves this green". There was no third outcome, and the
    first was taken SILENTLY: the reach set was derived as the locators unioned
    with the vocabulary MINUS the exclusions, so ``vocabulary - excluded <=
    reach set`` reduced to ``A <= B | A``. ``fchmod`` added to the vocabulary
    and classified nowhere left this test green - measured.

    **THE ASSERTION WAS NOT DELETED; THE DERIVATION WAS REPAIRED UNDER IT.**
    Inclusion is declared in
    :data:`~tests.save.reach_guard._REACHES_THE_LIBRARY` and
    :func:`~tests.save.reach_guard._reach_primitives` intersects rather than
    subtracts, so that same line now asserts something: every non-excluded
    vocabulary name must be DECLARED reaching, and an unclassified one is
    reported by name. The item's fence forbade closing it by deleting the
    assertion, which is what holds the exclusion direction.

    BOTH DIRECTIONS AND DISJOINTNESS ARE HELD, because a partition asserted one
    way round is a subset check wearing a partition's name.
    """
    excluded = frozenset(_NOT_LIBRARY_REACH)
    assert excluded <= _FILESYSTEM_PRIMITIVES, (
        f"an exclusion names something outside the vocabulary: "
        f"{sorted(excluded - _FILESYSTEM_PRIMITIVES)}"
    )
    assert (_FILESYSTEM_PRIMITIVES - excluded) <= _LIBRARY_PRIMITIVES, (
        f"vocabulary members are neither reach primitives nor excluded with a "
        f"reason: {sorted(_FILESYSTEM_PRIMITIVES - excluded - _LIBRARY_PRIMITIVES)}"
    )
    for name, reason in _NOT_LIBRARY_REACH.items():
        assert reason.strip(), f"{name} is excluded from the reach set with no reason"

    # NON-VACUITY, both halves. An empty vocabulary would satisfy the subset
    # assertions above, and so would a partition that excluded everything.
    assert _FILESYSTEM_PRIMITIVES, "the vocabulary is empty, so the partition is vacuous"
    assert _FILESYSTEM_PRIMITIVES - excluded, "every vocabulary member is excluded from reach"

    # The locators are NOT vocabulary and must not be smuggled into it: they are
    # project function names, and a partition over them would be meaningless.
    assert not (_LIBRARY_LOCATORS & _FILESYSTEM_PRIMITIVES), (
        f"a locator is being carried as filesystem vocabulary: "
        f"{sorted(_LIBRARY_LOCATORS & _FILESYSTEM_PRIMITIVES)}"
    )
    assert _LIBRARY_LOCATORS <= _LIBRARY_PRIMITIVES, "a locator dropped out of the reach set"

    # THE OTHER DIRECTION OF THE PARTITION, CS-497. The assertions above say
    # every vocabulary member is classified; these say every classification
    # names vocabulary, and that nothing is classified twice. Without them a
    # name could be declared reaching while sitting in no vocabulary at all,
    # which reads as a live rule and governs nothing.
    assert _REACHES_THE_LIBRARY <= _FILESYSTEM_PRIMITIVES, (
        f"these names are declared to reach the library and are not filesystem "
        f"vocabulary: {sorted(_REACHES_THE_LIBRARY - _FILESYSTEM_PRIMITIVES)}"
    )
    assert not (_REACHES_THE_LIBRARY & excluded), (
        f"these names are classified BOTH ways, so the partition is not one: "
        f"{sorted(_REACHES_THE_LIBRARY & excluded)}"
    )
    vocabulary = frozenset(_FILESYSTEM_PRIMITIVES)
    classified = _REACHES_THE_LIBRARY | excluded
    assert classified == vocabulary, (
        f"the two classifications do not cover the vocabulary exactly. "
        f"Unclassified: {sorted(vocabulary - classified)}; "
        f"classified but not vocabulary: {sorted(classified - vocabulary)}"
    )
    assert _REACHES_THE_LIBRARY, "nothing is declared to reach the library, so this is vacuous"


#: A module that reaches the library and says so nowhere. Written into tmp_path
#: by the control below rather than into this package, so the tracked tree is
#: untouched and the guard is put to a module it has genuinely not seen.
_UNDECLARED_MODULE_SOURCE: Final = """
from clockspeed.data import locate


def _helper_that_reaches():
    root = locate.resolve_save_root()
    return locate.resolve_account_dir(root)
"""

#: A module whose reaching helper hands its caller a DATACLASS holding a body.
#: This is CS-471's wrapper evasion in its smallest honest form.
_WRAPPED_BODY_MODULE_SOURCE: Final = """
from dataclasses import dataclass

from clockspeed.data import locate


@dataclass(frozen=True)
class _Wrapped:
    body: bytes


def _reaches_and_wraps() -> _Wrapped:
    root = locate.resolve_save_root()
    account = locate.resolve_account_dir(root)
    return _Wrapped(body=sorted(account.glob("*.sav"))[0].read_bytes())


def _takes_the_wrapper():
    return _reaches_and_wraps()
"""


def test_the_suite_wide_guard_catches_a_module_that_declares_nothing(tmp_path: Path) -> None:
    """CS-471 clauses 1 and 2, FORCED rather than asserted about.

    The suite-wide guard is green on this package, and a guard that is green can
    be green for two reasons: the package is declared, or the guard reports
    nothing whatever is put to it. This puts a module to it that reaches the
    library through the raw locators and carries no declarations, and requires
    the verdict to name it.

    IT IS WRITTEN INTO ``tmp_path`` AND NOT INTO THE PACKAGE, so no tracked file
    is created, no import cache is disturbed, and the run leaves the tree as it
    found it.

    It needs no save library - it is a claim about the repo, not about a world.
    """
    planted = tmp_path / "test_planted_undeclared.py"
    planted.write_text(_UNDECLARED_MODULE_SOURCE, encoding="utf-8")

    tree = ast.parse(planted.read_text(encoding="utf-8"))
    functions = _scanned_functions(tree)
    primitives = _effective_primitives(tree, _LIBRARY_PRIMITIVES, source=planted)
    reaching = [name for name, node in functions.items() if _calls_any(node, primitives)]
    assert reaching == ["_helper_that_reaches"], (
        f"the planted module was meant to reach the library and the scanner found "
        f"{reaching}. The control is describing a module that is not the one it wrote."
    )

    undeclared, rejected = _declaration_verdicts([planted], lambda _path: object())
    assert undeclared == [planted.name], (
        f"a module reaching the library through the raw locators and declaring "
        f"neither map was not reported: undeclared={undeclared}, "
        f"rejected={[one[0].name for one in rejected]}. "
        "The suite-wide guard would then be green on this package for a reason that "
        "has nothing to do with the package being declared."
    )


def test_a_helper_handing_back_a_wrapped_body_is_flagged_as_propagating(
    tmp_path: Path,
) -> None:
    """CS-471 clause 3 - the wrapper evasion, and the OLD rule failing it.

    BOTH RULES ARE RUN ON THE SAME NODE, which is what makes this a measurement
    of the widening rather than a restatement of it. The old rule read the
    rendered return annotation for ``Path`` or ``bytes``; a dataclass with a
    ``body: bytes`` field renders as neither, so a helper handing one back
    propagated the whole decompressed world past a guard that reported it clean.

    THE CONSEQUENCE IS GRADED TOO, not just the predicate. With the wrapper
    helper declared, its caller becomes an indirect reach site and the guard has
    to say so - which is the half that would still be missing if this only
    checked the boolean.

    THE LIVE INSTANCE IS NOT SYNTHETIC. ``tests/save/test_value_anchoring.py``
    ships ``_extents_of``, which hands back an ``_Extents`` holding a body; the
    old rule called it clean and the new one does not.

    IT CHANGES NO VERDICT ON THE SHIPPED PACKAGE TODAY, and that is disclosed
    rather than left to be discovered. ``_extents_of`` calls no primitive, so it
    is not a direct reach site and is not graded, and the propagation half is
    consulted for graded helpers alone. The widening is therefore latent on the
    real tree and live only on a module like the one planted here - which is
    exactly why it is planted rather than argued for.

    It needs no save library - it is a claim about the repo, not about a world.
    """
    planted = tmp_path / "test_planted_wrapper.py"
    planted.write_text(_WRAPPED_BODY_MODULE_SOURCE, encoding="utf-8")
    tree = ast.parse(planted.read_text(encoding="utf-8"))
    functions = _scanned_functions(tree)

    wrapping = _body_wrapping_classes(tree)
    assert wrapping == frozenset({"_Wrapped"}), (
        f"the body-wrapping class walk found {sorted(wrapping)} in a module whose "
        "only class holds a bytes field. The predicate below would then be "
        "measuring the walk's silence rather than the widening."
    )

    node = functions["_reaches_and_wraps"]
    assert not _returns_personal_data(node), (
        "the OLD rule already called a wrapped body personal, so this control "
        "grades nothing and CS-471's clause 3 had no defect to close. Either the "
        "planted module stopped wrapping or the narrow rule has changed."
    )
    assert _returns_personal_data(node, wrapping), (
        "the widened rule still calls a helper returning a dataclass with a "
        "bytes field clean, which is exactly the evasion CS-471 was filed on."
    )

    with pytest.raises(AssertionError) as caught:
        _assert_library_reach_is_declared(
            planted,
            graded={"_reaches_and_wraps": "reaches and hands back a wrapped body"},
            exempt={},
        )
    assert "_takes_the_wrapper" in str(caught.value), (
        "the caller of the wrapper-returning helper was not reported as an "
        f"undeclared indirect reach site. The guard said: {caught.value}"
    )


def test_the_module_that_owns_the_guard_is_inside_the_population_it_walks() -> None:
    """CS-495 - the self-guarding property, PINNED rather than left in prose.

    WHAT CS-495 CLAIMED AND WHAT WAS ACTUALLY HOLDING IT. Moving the guard out of
    ``test_properties`` was argued on the ground that CS-471's package walk
    covers every module in this directory, so the guard grades its own source
    wherever it lives. That is true, and until this test nothing enforced it: a
    MEASURED MUTANT narrowing :func:`~tests.save.reach_guard._reaching_modules`
    from ``*.py`` to ``test_*.py`` left the whole suite GREEN with the guard's
    own module silently outside the population it walks.

    THE MUTANT SURVIVED ON THE PRE-MOVE TREE TOO, so this is not a hole the
    relocation opened - it is one the relocation made load-bearing. Before the
    move the only non-test module here was the synthetic corpus, which reaches
    nothing and declares nothing, so narrowing the glob changed no verdict at
    all. After it, the same edit drops the guard itself out of scope.

    THE OWNER IS DERIVED, NEVER WRITTEN DOWN. It comes from the guard function's
    own code object, so if the implementation moves again this test follows it
    rather than pinning a filename that has stopped being true. A name spelled
    here would be the transcription the whole guard exists to avoid.

    It needs no save library - it is a claim about the repo, not about a world.
    """
    reaching, silent = _reaching_modules()
    walked = {path.name for path in (*reaching, *silent)}

    assert len(walked) > 1, (
        f"the package walk found {sorted(walked)}, which is too few modules for "
        "the membership assertion below to mean anything. Either the package "
        "moved or the walk has stopped enumerating it."
    )

    owner = Path(_assert_library_reach_is_declared.__code__.co_filename).name
    assert owner in walked, (
        f"{owner} defines the reach guard and is not in the population that guard "
        f"is applied to: {sorted(walked)}. A guard outside its own scope is the "
        "arrangement that let a third sweep ship ungraded one file over, and it "
        "is the exact objection CS-495 answered by pointing at this walk."
    )


def test_no_module_the_collector_skips_defines_a_test() -> None:
    """A test in a module pytest never collects runs zero times and says nothing.

    THE HOLE THIS CLOSES WAS MEASURED, NOT IMAGINED. A refutation pass on CS-495
    appended a gutted test - ``return`` before a ``raise`` - to
    ``tests/save/reach_guard.py`` and the whole repo suite stayed GREEN, while
    the same append to the module that owned the guard BEFORE the relocation
    reddened two tests. The merger reproduced both, and reproduced a third: the
    same append to ``tests/save/synthetic.py`` also survives, on this tree and
    on the pre-relocation one.

    SO THE CLASS IS OLDER THAN CS-495 AND THE EXPOSURE IS NEW. Before the move
    the only uncollected module in this package was the synthetic corpus, which
    defines no test and never would. Moving the guard implementation into a
    second uncollected module put a file that people will want to add checks to
    inside the same blind spot. Nothing is stranded today - both modules are
    asserted below to define nothing - and this test is what keeps that true.

    IT IS A CLAIM ABOUT THE COLLECTOR, NOT ABOUT THE GUARD, and it lives here
    because this module already owns the claims about which modules the package
    walk covers. It reads that same walk rather than globbing again, so it
    cannot disagree with it about the population.

    NEITHER RUFF NOR MYPY COVERS THIS. Both read the uncollected module happily
    - a planted violation in it is reported by each - which is precisely why a
    dead test in it looks healthy to every tool in the tree.

    It needs no save library - it is a claim about the repo, not about a world.
    """
    reaching, silent = _reaching_modules()
    uncollected = [path for path in (*reaching, *silent) if not path.name.startswith("test_")]

    assert uncollected, (
        "every module in this package is collected by pytest, so this guard is "
        "vacuous. It exists for the modules that are NOT - if there are none, "
        "either the package changed shape or the walk stopped enumerating it."
    )

    stranded: dict[str, list[str]] = {}
    for path in uncollected:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = [name for name in _scanned_functions(tree) if name.startswith("test_")]
        names += [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and node.name.startswith("Test")
        ]
        if names:
            stranded[path.name] = sorted(names)

    assert not stranded, (
        f"these modules are not collected by pytest and define tests anyway: "
        f"{stranded}. Every one of those runs zero times, passes nothing and "
        "fails nothing, and appears in no suite listing where a reader would "
        "miss it. Move them into a module named test_*.py, or rename them so "
        "they do not read as tests."
    )


#: How many copies of the guard's source the name-independence control judges.
#: Named so the count in its assertion is not a bare literal that could drift
#: away from the loop above it.
_COPIES_OF_THE_GUARD_SOURCE: Final = 2

#: An uncontained helper appended to a COPY of the guard's own source. Spelled
#: once because two controls splice it - one grading that the guard has teeth
#: over its own file at all, one grading that those teeth do not depend on what
#: the file is called.
_UNCONTAINED_GUARD_SPLICE: Final = (
    "\n\ndef _spliced_uncontained_guard_helper():\n"
    '    """A helper carrying the known-bad shape."""\n'
    "    from clockspeed.data import locate\n"
    "\n"
    "    root = locate.resolve_save_root()\n"
    "    return locate.resolve_account_dir(root)\n"
)


def test_the_guard_reaches_the_same_verdict_under_its_own_name_as_under_any_other(
    tmp_path: Path,
) -> None:
    """CS-498 - a guard that early-returns on its own file name is caught.

    WHAT WAS WRONG, MEASURED ON TWO TREES. Every control over this guard runs it
    against a ``tmp_path`` COPY under a different filename, so a guard that
    early-returned on its own name defeated all of them at once: the planted
    splice still reddened, every positive control still passed, and an
    undeclared reaching helper in the guard's REAL source went unseen. Adding
    ``if module_path.name == "<its own file>": return`` to
    :func:`~tests.save.reach_guard._assert_library_reach_is_declared` AND
    appending an undeclared helper to that same file left ``tests/save`` green -
    on the post-CS-495 tree and on ``1e05233``, where the guard still lived in
    ``test_properties``. The relocation neither caused it nor worsened it.

    THE CLOSE NAMES NO FILENAME, WHICH IS THE ITEM'S FENCE. Writing the guard's
    own basename into a control would be the same defect pointing the other way
    - a second place that has to be updated when the file moves, and one that
    goes quiet rather than red when it is not. The basename is taken from the
    guard's own code object and a copy is written under it in ``tmp_path``, so
    the control follows the implementation wherever it goes.

    THE COMPARISON IS THE POINT, NOT EITHER VERDICT. Two byte-identical copies
    of the same spliced source, differing only in what they are called, must get
    the same answer. A name-keyed exemption breaks that equality; nothing a
    correct guard does can.

    WHAT IT DOES NOT REACH, stated rather than implied. An exemption keyed on
    the guard's full PATH rather than its name survives this: both copies live
    in ``tmp_path`` and neither is the real file, so both are judged normally
    and they agree. That shape cannot be caught without editing the tracked
    source, and nothing here claims otherwise.

    Args:
        tmp_path: The per-test temporary directory.
    """
    owner = Path(_assert_library_reach_is_declared.__code__.co_filename)
    spliced_source = owner.read_text(encoding="utf-8") + _UNCONTAINED_GUARD_SPLICE

    under_its_own_name = tmp_path / "same_name" / owner.name
    under_another_name = tmp_path / "other_name" / "a_module_this_guard_has_never_seen.py"
    assert under_its_own_name.name != under_another_name.name, (
        "both copies carry the same filename, so this control cannot tell a "
        "name-keyed exemption from a correct guard"
    )

    for target in (under_its_own_name, under_another_name):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(spliced_source, encoding="utf-8")

    # ``pytest.raises`` RATHER THAN A TRY/EXCEPT, and that is non-negotiable 12
    # rather than style. Binding the exception in an ``except`` handler and
    # rendering it is the shape ``tests/test_exception_rendering.py`` forbids -
    # ``str`` on an OSError appends the path it failed on. It caught the first
    # draft of this control. A copy that does NOT raise fails here with pytest's
    # own DID NOT RAISE, naming the copy, which is the verdict this grades.
    named: list[str] = []
    for target in (under_its_own_name, under_another_name):
        with pytest.raises(AssertionError) as caught:
            _assert_library_reach_is_declared(
                target,
                graded=reach_guard._GRADED_LIBRARY_REACH,  # noqa: SLF001
                exempt=reach_guard._EXEMPT_LIBRARY_REACH,  # noqa: SLF001
            )
        if "_spliced_uncontained_guard_helper" in str(caught.value):
            named.append(target.name)

    assert len(named) == _COPIES_OF_THE_GUARD_SOURCE, (
        f"the guard named the spliced helper in {named} and not in both copies. Two "
        "byte-identical sources that differ only in filename got different answers, "
        "which is what a self-exemption keyed on the guard's own name looks like "
        "from outside."
    )


def test_the_guard_catches_an_uncontained_helper_spliced_into_its_own_source(
    tmp_path: Path,
) -> None:
    """The guard's POWER over its OWN source, forced rather than asserted about.

    WHAT THIS RESTORES. Every module that consumes the guard carries a control
    splicing an uncontained helper into a copy of its own source and requiring
    the guard to name it. Before CS-495 the guard lived in such a module and got
    that control for free; a refutation pass measured the cost of the move as a
    drop from ELEVEN tests reddening on an undeclared reach planted in the
    guard's own file to ONE. The property was still graded and the margin was a
    single test wide. This is the second one.

    THE SOURCE IS DERIVED FROM THE GUARD'S OWN CODE OBJECT, never named, so this
    control follows the implementation if it moves again rather than pinning a
    path that has stopped being true.

    WHAT IT DOES NOT REACH, stated rather than implied, because a control read as
    covering more than it does is the failure class this package has already paid
    for. The splice goes into ``tmp_path`` under a DIFFERENT FILENAME, so a guard
    that early-returns on its own file name defeats this control and every other
    one in the package at once: the splice still reddens, the positive control
    still passes, and an undeclared reach in the guard's real source goes unseen.
    That is measured, on this tree AND on the pre-relocation one, and it is filed
    as CS-498. Nothing here claims otherwise.

    Args:
        tmp_path: The per-test temporary directory.
    """
    owner = Path(_assert_library_reach_is_declared.__code__.co_filename)
    spliced = tmp_path / "spliced_guard.py"
    spliced.write_text(
        owner.read_text(encoding="utf-8") + _UNCONTAINED_GUARD_SPLICE, encoding="utf-8"
    )

    with pytest.raises(AssertionError) as caught:
        _assert_library_reach_is_declared(
            spliced,
            graded=reach_guard._GRADED_LIBRARY_REACH,  # noqa: SLF001
            exempt=reach_guard._EXEMPT_LIBRARY_REACH,  # noqa: SLF001
        )
    assert "_spliced_uncontained_guard_helper" in str(caught.value), (
        "the guard reddened on its own spliced source without naming the evader, "
        "so it failed for some other reason and this route is still unmeasured"
    )

    # The positive control: the same guard on the unspliced source passes, so
    # the red above is the splice rather than the guard rejecting everything.
    _assert_library_reach_is_declared(
        owner,
        graded=reach_guard._GRADED_LIBRARY_REACH,  # noqa: SLF001
        exempt=reach_guard._EXEMPT_LIBRARY_REACH,  # noqa: SLF001
    )


def test_every_library_reaching_module_in_the_package_is_declared() -> None:
    """CS-471 clauses 1 and 2 - the guard no module has to opt into.

    WHAT WAS WRONG, MEASURED BEFORE THIS TEST EXISTED. The reach guard was
    consumed by whichever module remembered to call it; a minority of the modules
    under ``tests/save`` did, and the rest were unexamined. Several of those had
    functions touching a library primitive, and a NEW library-reaching module
    shipped undeclared by default - the opposite of what a privacy guard should
    do on the path of least effort. NO COUNT IS QUOTED HERE, deliberately: the
    figures live in the CS-471 ledger entry, which is dated, and a measured
    number in prose is a lie with a timestamp on it.

    WHAT THIS DOES NOT REACH, because a green guard invites the wrong reading. A
    module with no direct primitive call is classed silent and skipped, so a
    helper imported from a sibling and called here is invisible to the
    enumeration. This proves the guard is APPLIED to every module in the package;
    it does not prove every route into the library runs through a primitive this
    module names.

    THE ENUMERATION IS THE POINT AND IT IS NOT A LIST. This walks the package's
    own directory, so a module added tomorrow is in scope the moment it exists.
    A guard that had to be added to each new module is exactly the guard that
    was not added to eleven.

    BOTH DIRECTIONS ARE HELD. A module that reaches must declare; a module that
    does NOT reach must not carry declarations, or an exemption outlives the
    code it described and the next reader inherits a reason for nothing. The
    second half is what stops this test being satisfied by pasting empty maps
    into every file.

    THE PER-MODULE TESTS ARE NOT REDUNDANT AND ARE DELIBERATELY KEPT. Each
    consuming module also carries a splice control that forces the guard to
    catch a planted uncontained helper IN THAT MODULE. This test proves the
    guard is APPLIED everywhere; those prove it has teeth. Neither is the other,
    and the count of consumers is not a claim about the count of modules walked.
    THIS SENTENCE USED TO NAME BOTH NUMBERS. The second was already stale when it
    was written and CS-495 made it staler; both are dropped rather than
    re-measured, for the reason CLAUDE.md section 4 gives.

    It needs no save library - it is a claim about the repo, not about a world.
    """
    reaching, silent = _reaching_modules()
    assert reaching, (
        "no module under tests/save has a function touching a library primitive, "
        "so this guard is vacuous. Either the package moved or the primitive "
        "vocabulary has stopped matching the code it describes."
    )

    undeclared, rejected = _declaration_verdicts(reaching, _imported_sibling)

    assert not undeclared, (
        f"these modules have a function touching a library primitive and declare "
        f"nothing: {sorted(undeclared)}. Each needs "
        f"{_REACH_DECLARATIONS[0]} and {_REACH_DECLARATIONS[1]} at module scope - "
        "every reaching function either graded with why it reaches, or exempt with "
        "why touching a primitive is not reaching the library here. A module that "
        "declares nothing is not a module that reaches nothing."
    )
    if rejected:
        # RE-RAISED THROUGH THE GUARD rather than rendered from a caught object,
        # so the message pytest shows is the guard's own and this frame holds no
        # exception at all - see the note in _declaration_verdicts.
        path, graded, exempt = rejected[0]
        _assert_library_reach_is_declared(path, graded=graded, exempt=exempt)

    stray = [
        path.name
        for path in silent
        if any(
            getattr(importlib.import_module(f"tests.save.{path.stem}"), name, None) is not None
            for name in _REACH_DECLARATIONS
        )
    ]
    assert not stray, (
        f"{sorted(stray)} carry library-reach declarations and no function in them "
        "touches a primitive at all. A declaration that outlives the code it "
        "described reads as a live constraint and holds nothing - delete it, or "
        "the next reader inherits a reason for something that is not there."
    )
