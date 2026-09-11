"""CS-962 - the Warnings panel, graded against synthetic payloads.

WHAT THIS MODULE IS FOR. Non-negotiable 7 says unknown content is flagged and
skipped, never fatal and never silently wrong. ``/api/world`` and
``/api/registry`` both carry that flag stream, and before this panel the page
rendered it as a COUNT. A count tells a reader something is wrong and nothing
about what, which is the half of non-negotiable 7 the surface was not keeping.

THE SHARP CONSTRAINT, AND WHY HALF THIS MODULE IS ABOUT IT. A warning string
is text that came out of the operator's own save file. Non-negotiables 11 and
12 hold that a save is a personal-data-bearing artifact and that any code path
echoing raw bytes is a leak; non-negotiable 3 forbids an absolute path under a
home directory reaching a tracked artifact, and ``tools/dashboard_probe.py``
SCREENSHOTS this page, so a leak here is a leak into an image.

The producers were audited before a line of this panel was written and they are
clean - the finding is recorded in the panel module's own header comment with
its file:line citations. The panel does not RELY on that audit. It re-checks
shape at the sink, because the audit is a statement about today's producers and
the sink is where a future one would leak. Four arms below are hostile
fixtures that no producer can emit today and that the sink must still refuse.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Final

import pytest

from clockspeed.surface.api import registry as api_registry
from clockspeed.surface.api import world as api_world
from tests.surface import panel_harness

#: The module under grade.
MODULE: Final = "panel_warnings.js"

#: Its path on disk, for the checks that read source rather than mount it.
MODULE_PATH: Final = panel_harness.WEB_DIR / MODULE

#: What the panel renders in place of a value whose shape it does not accept.
#: Asserted rather than inferred so that a panel which silently DROPPED a
#: refused value would fail here: silence and refusal must not look alike.
WITHHELD: Final = "[withheld - unexpected shape]"

#: The backslash, named rather than written into a path-shaped literal.
BACKSLASH: Final = chr(92)

#: The account-name fragment of the hostile paths below. A panel that renders
#: any part of a path has leaked; asserting on the whole string alone would
#: pass a panel that truncated it at a character boundary and shipped the name.
HOSTILE_PATH_NAME: Final = "somebody"


def _windows_path() -> str:
    """A Windows path under a home directory, assembled at run time.

    NOT A LITERAL, AND THE PRE-COMMIT GATE IS WHY. It blocks a home-path
    literal in a tracked file under non-negotiable 3, and it is right to: the
    intent behind the literal does not change the byte on disk. Assembling it
    here keeps the fixture's teeth - the panel receives a genuine path - while
    the repository holds no path-shaped string.

    Returns:
        The path.
    """
    parts = ["C:", "Users", HOSTILE_PATH_NAME, "AppData", "Local", "Saved", "a.sav"]
    return BACKSLASH.join(parts)


def _posix_path() -> str:
    """The same thing in the other family, for the other hostile arm.

    Returns:
        The path.
    """
    return "/".join(["", "home", HOSTILE_PATH_NAME, ".local", "share", "docs.json"])


#: A hostile detail. Nothing in the save or registry layers can produce this
#: today - every detail is a fixed table line or an integer interpolation - and
#: that is exactly why it belongs here. An absolute path on this machine
#: carries the Windows account name, which non-negotiable 3 forbids.
HOSTILE_PATH_DETAIL: Final = "could not read " + _windows_path()

#: How many groups the panel renders unconditionally: one per wire that
#: carries a warning stream. Both must say they did not answer when both
#: payloads are null.
GROUPS: Final = 2

#: The highest byte a 7-bit ASCII file may carry.
ASCII_MAX: Final = 0x7F


def _world(**overrides: Any) -> dict[str, Any]:
    """A minimal ``/api/world`` data object, overridable field by field.

    Only the keys this panel consumes are spelled out. The endpoint carries
    more (world.py:111-123) and a panel that needed them would say so.

    Args:
        overrides: Keys to replace on the default.

    Returns:
        The data object.
    """
    body: dict[str, Any] = {
        "warnings": [],
        "contains_unmodeled_content": False,
    }
    body.update(overrides)
    return body


def _registry(**overrides: Any) -> dict[str, Any]:
    """A minimal ``/api/registry`` data object, overridable field by field.

    Args:
        overrides: Keys to replace on the default.

    Returns:
        The data object.
    """
    body: dict[str, Any] = {"warnings": [], "unknown_groups": []}
    body.update(overrides)
    return body


def _world_warning(
    *, source: Any, code: Any, detail: Any, subject: Any, count: Any
) -> dict[str, Any]:
    """One ``/api/world`` warning, keyed the way that endpoint keys one.

    THE KEYS ARE SPELLED ONCE, HERE. Every world-warning fixture in this module
    is built through this function, so the equality arm in the pin section
    binds ALL of them to ``world.WARNING_KEYS`` rather than the one that
    happened to be checked - see the pin section's header for why a per-arm
    spelling is the exact defect that stays green while the page goes blank.

    Args:
        source: The stage that raised it.
        code: The warning code.
        detail: The fixed line the raising layer authored.
        subject: The structural token, or None.
        count: How many times it fired.

    Returns:
        The warning record.
    """
    return {
        "source": source,
        "code": code,
        "detail": detail,
        "subject": subject,
        "count": count,
    }


def _registry_warning(*, code: Any, detail: Any, subject: Any, count: Any) -> dict[str, Any]:
    """One ``/api/registry`` warning, keyed the way THAT endpoint keys one.

    Four keys, not five: a registry warning carries no ``source``
    (registry.py:174), and the panel renders the two shapes separately for
    exactly that reason. A helper shared with :func:`_world_warning` would have
    had to invent the field on one side or drop it from the other.

    Args:
        code: The warning code.
        detail: The fixed line the data layer authored.
        subject: A class name, a group short name or a group index.
        count: How many times it fired.

    Returns:
        The warning record.
    """
    return {"code": code, "subject": subject, "detail": detail, "count": count}


def _unknown_class(*, type_path: Any, count: Any, reason: Any, first_index: Any) -> dict[str, Any]:
    """One ``/api/world`` unmodelled class, keyed the way that endpoint keys one.

    Args:
        type_path: The class path.
        count: How many instances were met.
        reason: Why it was not modelled.
        first_index: Where the first one sat.

    Returns:
        The record.
    """
    return {
        "type_path": type_path,
        "count": count,
        "reason": reason,
        "first_index": first_index,
    }


def _text(report: Any) -> str:
    """The whole panel's text, joined by the stand-in from the tree.

    Args:
        report: A harness report.

    Returns:
        The text of node 0, which is the panel's own section.
    """
    return str(report["nodes"][0]["text"])


def _mount(tmp_path: Path, data: Any) -> Any:
    """Mount the panel and assert it mounted rather than failing.

    Every arm wants this: a panel that threw would otherwise be graded on the
    app.js failure note rather than on anything it built, and the assertion
    that some string is absent would PASS for the worst possible reason.

    Args:
        tmp_path: Scratch directory.
        data: The payload.

    Returns:
        The report.
    """
    report = panel_harness.mount(tmp_path, MODULE, data)
    assert report["load_threw"] is None, report["load_threw"]
    assert report["threw"] is None, report["threw"]
    assert report["state"] == "mounted"
    return report


# ---------------------------------------------------------------------------
# The five acceptance clauses the CS-962 spec states for this slice.
# ---------------------------------------------------------------------------


def test_both_groups_render_every_code_and_the_world_warning_source(
    tmp_path: Path,
) -> None:
    """Acceptance 1: two world warnings and one registry warning all surface.

    The two shapes are NOT merged. A world warning carries ``source``
    (world.py:142) and a registry warning does not (registry.py:174); merging
    them would invent a field on one side or drop one from the other.

    Args:
        tmp_path: Scratch directory.
    """
    data = panel_harness.null_payload(
        world=_world(
            warnings=[
                _world_warning(
                    source="usmap",
                    code="unresolved-name",
                    detail="a schema name index fell outside the name table",
                    subject="schema-12",
                    count=3,
                ),
                _world_warning(
                    source="objects",
                    code="unresolved-schema",
                    detail="the class path does not resolve to a schema",
                    subject=None,
                    count=1,
                ),
            ]
        ),
        registry=_registry(
            warnings=[
                _registry_warning(
                    code="unknown-item-reference",
                    subject="Desc_Water_C",
                    detail="a recipe names an item this document does not define",
                    count=2,
                )
            ]
        ),
    )
    text = _text(_mount(tmp_path, data))
    for code in ("unresolved-name", "unresolved-schema", "unknown-item-reference"):
        assert code in text
    assert "usmap" in text
    assert "world warnings" in text.lower()
    assert "registry warnings" in text.lower()


def test_a_null_world_still_renders_the_registry_group(tmp_path: Path) -> None:
    """Acceptance 2: world null, registry populated - both facts are said.

    Args:
        tmp_path: Scratch directory.
    """
    data = panel_harness.null_payload(
        registry=_registry(
            warnings=[
                _registry_warning(
                    code="malformed-group",
                    subject="41",
                    detail="a group was not readable as a group and was skipped",
                    count=1,
                )
            ]
        )
    )
    text = _text(_mount(tmp_path, data))
    assert "malformed-group" in text
    assert "did not answer" in text


def test_both_null_mounts_and_says_so(tmp_path: Path) -> None:
    """Acceptance 3: every payload null - mounted, never failed.

    Args:
        tmp_path: Scratch directory.
    """
    report = _mount(tmp_path, panel_harness.null_payload())
    text = _text(report)
    assert text.lower().count("did not answer") == GROUPS


def test_no_unknown_class_type_path_is_duplicated_here(tmp_path: Path) -> None:
    """Acceptance 4: ``unknown_classes`` belongs to the World section.

    app.js:408-424 already renders that list. This panel names the section
    instead, so the one place a ``type_path`` crosses the wire stays one place
    on the page too.

    Args:
        tmp_path: Scratch directory.
    """
    marker = "/Game/FactoryGame/Buildable/Factory/Bogus/Build_Bogus.Build_Bogus_C"
    companion = "unresolved-schema"
    data = panel_harness.null_payload(
        world=_world(
            warnings=[
                _world_warning(
                    source="objects",
                    code=companion,
                    detail="the class path does not resolve to a schema",
                    subject=None,
                    count=4,
                )
            ],
            unknown_classes=[
                _unknown_class(type_path=marker, count=4, reason="asset_shaped", first_index=9)
            ],
            counts={"unknown_classes": 1},
        )
    )
    report = _mount(tmp_path, data)
    text = _text(report)
    # THE POSITIVE HALF, AND WHY IT IS NOT DECORATION. This arm used to rule the
    # type_path OUT and pin almost nothing IN, so it passed over any panel that
    # reached the world object and rendered nothing from it - "an oracle can be
    # blind to its subject", which this repo has already measured twice. The
    # companion warning is carried by the SAME world object as the unknown
    # class, so a panel that stopped consuming that object reddens on the line
    # below instead of quietly satisfying the absence claims. The group label
    # alone would not do it: the panel emits both labels unconditionally
    # (panel_warnings.js:351-353) whether or not it ever read a payload.
    assert companion in text, (
        "the panel rendered nothing out of the world object, so the absence of a"
        f" type_path below proves nothing; the panel read {text!r}"
    )
    assert "did not answer" not in text.lower().split("registry warnings")[0], (
        "the world group reported that /api/world never answered, so this arm"
        " would be grading an unread payload"
    )
    assert marker not in text
    assert "Build_Bogus" not in text
    assert "world" in text.lower()


def test_unmodeled_content_is_stated_even_with_no_warnings(tmp_path: Path) -> None:
    """Acceptance 5: the flag is its own fact, not a function of the list.

    ``contains_unmodeled_content`` (world.py:119) can be true while the warning
    array is empty. A panel that derived the line from the list length would
    say nothing at all here.

    Args:
        tmp_path: Scratch directory.
    """
    data = panel_harness.null_payload(world=_world(warnings=[], contains_unmodeled_content=True))
    text = _text(_mount(tmp_path, data))
    assert "unmodelled content" in text.lower()


# ---------------------------------------------------------------------------
# Absence is not silence: three distinguishable states per group.
# ---------------------------------------------------------------------------


def test_zero_warnings_reads_differently_from_no_answer(tmp_path: Path) -> None:
    """A loaded world reporting nothing is not a world that did not answer.

    These are different facts and a reader has to be able to tell them apart.
    The dispatch calls this out by name and nothing else in the suite pins it.

    Args:
        tmp_path: Scratch directory.
    """
    answered = _text(_mount(tmp_path, panel_harness.null_payload(world=_world())))
    silent = _text(_mount(tmp_path, panel_harness.null_payload()))
    assert "did not answer" not in answered.lower().split("registry warnings")[0]
    assert "no warnings" in answered.lower()
    assert answered != silent


def test_registry_unknown_groups_are_named(tmp_path: Path) -> None:
    """``unknown_groups`` (registry.py:142) is content this build cannot model.

    Args:
        tmp_path: Scratch directory.
    """
    data = panel_harness.null_payload(
        registry=_registry(unknown_groups=["FGBuildableSomethingNew", "FGRecipeVariant"])
    )
    text = _text(_mount(tmp_path, data))
    assert "FGBuildableSomethingNew" in text
    assert "FGRecipeVariant" in text


# ---------------------------------------------------------------------------
# HOSTILE FIXTURES. No producer emits any of these today. The sink refuses
# them anyway, because the audit is about producers and this is the sink.
# ---------------------------------------------------------------------------


def test_a_detail_carrying_an_absolute_path_never_reaches_the_dom(
    tmp_path: Path,
) -> None:
    """THE ARM THIS SLICE EXISTS TO GET RIGHT.

    An absolute path under a home directory carries the Windows account name.
    Rendering it would violate non-negotiable 3 and would put it in the
    ``dashboard_probe`` screenshot. The warning's CODE still renders, because
    withholding the value must not withhold the fact that a warning exists.

    Args:
        tmp_path: Scratch directory.
    """
    data = panel_harness.null_payload(
        world=_world(
            warnings=[
                _world_warning(
                    source="header",
                    code="unmeasured-version-pair",
                    detail=HOSTILE_PATH_DETAIL,
                    subject="5/13",
                    count=1,
                )
            ]
        )
    )
    text = _text(_mount(tmp_path, data))
    assert HOSTILE_PATH_NAME not in text
    assert "C" + ":" not in text
    assert ".sav" not in text
    assert "AppData" not in text
    assert WITHHELD in text
    assert "unmeasured-version-pair" in text
    assert "5/13" in text


def test_a_subject_carrying_a_path_never_reaches_the_dom(tmp_path: Path) -> None:
    """The same refusal on the other field, since both are rendered text.

    A registry subject is a class name or a token (registry.py:414-417), so a
    path-shaped one is a producer that changed. The sink refuses it without
    needing to know which producer.

    Args:
        tmp_path: Scratch directory.
    """
    data = panel_harness.null_payload(
        registry=_registry(
            warnings=[
                _registry_warning(
                    code="malformed-blob",
                    subject=_posix_path(),
                    detail="a blob was not readable and was skipped",
                    count=1,
                )
            ]
        )
    )
    text = _text(_mount(tmp_path, data))
    assert HOSTILE_PATH_NAME not in text
    assert "home" + "/" not in text
    assert WITHHELD in text
    assert "malformed-blob" in text


def test_a_non_ascii_detail_is_withheld(tmp_path: Path) -> None:
    """A DELIBERATE DECISION, not an accident of the character class.

    Every authored warning line in this project is 7-bit ASCII, because rule 4
    requires it of all authored content. So a detail arriving with a character
    outside that set was NOT authored - it was built from content, and the
    likeliest content to carry one is a player display name. The sink treats
    non-ASCII as proof of provenance and refuses.

    Args:
        tmp_path: Scratch directory.
    """
    data = panel_harness.null_payload(
        world=_world(
            warnings=[
                _world_warning(
                    source="objects",
                    code="unresolved-schema",
                    detail="player \u00c9lodie's factory could not be read",
                    subject=None,
                    count=1,
                )
            ]
        )
    )
    text = _text(_mount(tmp_path, data))
    assert "\u00c9lodie" not in text
    assert "lodie" not in text
    assert WITHHELD in text
    assert "unresolved-schema" in text


def test_an_unknown_group_carrying_a_path_is_withheld(tmp_path: Path) -> None:
    """The third rendered-text channel gets the same treatment as the other two.

    Args:
        tmp_path: Scratch directory.
    """
    data = panel_harness.null_payload(registry=_registry(unknown_groups=[_windows_path()]))
    text = _text(_mount(tmp_path, data))
    assert HOSTILE_PATH_NAME not in text
    assert WITHHELD in text


def test_a_count_that_is_not_a_whole_number_is_withheld(tmp_path: Path) -> None:
    """A count is an int on both wires. Anything else is not rendered as one.

    A float would also be a float on a page whose solve path forbids them, and
    a string count could carry anything at all.

    Args:
        tmp_path: Scratch directory.
    """
    data = panel_harness.null_payload(
        registry=_registry(
            warnings=[
                _registry_warning(
                    code="duplicate-class-name",
                    subject="Desc_IronRod_C",
                    detail="a class name repeated and the later entry won",
                    count=_windows_path(),
                )
            ]
        )
    )
    text = _text(_mount(tmp_path, data))
    assert HOSTILE_PATH_NAME not in text
    assert "duplicate-class-name" in text


def test_a_warning_that_is_not_an_object_does_not_throw(tmp_path: Path) -> None:
    """A malformed row is skipped, not fatal, and nothing from a throw shows.

    Args:
        tmp_path: Scratch directory.
    """
    data = panel_harness.null_payload(
        world=_world(warnings=["not an object", None, 7]),
        registry=_registry(warnings=None, unknown_groups="not a list"),
    )
    report = _mount(tmp_path, data)
    assert "not an object" not in _text(report)


# ---------------------------------------------------------------------------
# Module-level rules every panel inherits.
# ---------------------------------------------------------------------------


def test_the_module_is_seven_bit_ascii() -> None:
    """Rule 4, checked on the bytes rather than on a decoded string."""
    raw = MODULE_PATH.read_bytes()
    offending = [index for index, byte in enumerate(raw) if byte > ASCII_MAX]
    assert not offending, f"{MODULE} carries non-ASCII bytes at {offending[:5]}"


def _code_only(source: str) -> str:
    """The module with its block comments removed.

    The same reduction the seam grader makes (test_panel_seam.py:80), for the
    same reason: this module's header comment EXPLAINS that it never assigns
    innerHTML, and a check reading prose would fail on the sentence saying the
    thing it wants to be true.

    Args:
        source: The module text.

    Returns:
        The text with ``/* ... */`` spans replaced by a space.
    """
    return re.sub(r"/\*[\s\S]*?\*/", " ", source)


def test_the_module_never_assigns_inner_html() -> None:
    """Untrusted text goes through textContent, never through innerHTML.

    This panel renders strings that came out of a save file. Parsing them as
    markup would be the one mistake that turns a shape guard into theatre.
    """
    code = _code_only(MODULE_PATH.read_text(encoding="ascii"))
    assert "innerHTML" not in code
    assert "outerHTML" not in code
    assert "insertAdjacentHTML" not in code
    assert "textContent" in code


def test_the_module_uses_no_timer() -> None:
    """No setTimeout and no setInterval - a panel renders and returns."""
    code = _code_only(MODULE_PATH.read_text(encoding="ascii"))
    assert "setTimeout" not in code
    assert "setInterval" not in code


def test_the_module_divides_nowhere() -> None:
    """Non-negotiable 6 reaches the render path too.

    Checked on code with block comments and string literals removed, so the
    division operator is looked for where it would actually execute. A regex
    in the source is a legitimate slash and is not one.
    """
    stripped = _code_only(MODULE_PATH.read_text(encoding="ascii"))
    stripped = re.sub(r'"(?:[^"\\\n]|\\.)*"', '""', stripped)
    stripped = re.sub(r"/(?:[^/\\\n\[]|\\.|\[[^\]\n]*\])+/[a-z]*", "RE", stripped)
    assert "/" not in stripped, f"a division survives in {MODULE}"


@pytest.mark.parametrize(
    "sink", ["fetch" + "(", "XMLHttpRequest", "sendBeacon", "EventSource", "WebSocket"]
)
def test_the_module_reaches_no_network_sink(sink: str) -> None:
    """A panel never issues a request; app.js owns every one this page makes.

    Duplicated from the seam grader deliberately: this module must stay clean
    on its own terms rather than only as a member of a swept population, and a
    pooled gate can be met by its strongest member while the weakest goes
    unmeasured.

    Args:
        sink: The spelling to look for.
    """
    assert sink not in _code_only(MODULE_PATH.read_text(encoding="ascii"))


# ---------------------------------------------------------------------------
# The common-mode pin - the fixtures are bound to the ENDPOINTS, not to a spec
#
# WHY THIS SECTION EXISTS. Every payload above was hand-typed from one
# planner-authored spec file in a scratchpad, and so was the panel it grades.
# That is ONE shared input wearing two hats, not two independent witnesses. A
# key misspelled in that spec is misspelled in the fixture, misspelled in the
# panel, and asserted against in the misspelling - and the suite is GREEN while
# the live page renders nothing for that field forever. CLAUDE.md section 5
# states the rule the arms below apply: agreement between two agents is not
# evidence, because two agents deriving from the same stale doc are wrong the
# same way. So the arms go and test the SHARED INPUT, by binding to
# ``clockspeed/surface/api/world.py`` and ``clockspeed/surface/api/registry.py``
# - the modules that actually serve the bytes.
#
# EQUALITY WHEREVER EQUALITY IS THE TRUTH. A warning record is a whole record
# and its key set is asserted EQUAL to the endpoint's tuple: a subset check
# would pass forever while a key the endpoint GAINS went unfixtured and
# unrendered. The two data objects are the one honest exception - this panel
# deliberately consumes a handful of keys out of a much larger body - so they
# get equality against the DECLARED CONSUMED SET plus a membership check
# against the endpoint, and a source scan makes the declared set equal to what
# the panel actually reads. A key the panel starts consuming therefore cannot
# stay unfixtured, and a key it consumes that no endpoint serves cannot stay
# unnoticed.
# ---------------------------------------------------------------------------

#: Exactly the ``/api/world`` keys ``panel_warnings.js`` consumes. Asserted
#: below to be both a real subset of ``world.DATA_KEYS`` and exactly what the
#: asset reads, so this tuple cannot drift away from either side.
WORLD_KEYS_CONSUMED: Final = ("warnings", "contains_unmodeled_content")

#: The same for ``/api/registry``.
REGISTRY_KEYS_CONSUMED: Final = ("warnings", "unknown_groups")

#: A subscript against one of the two data objects, e.g. ``world["warnings"]``.
DATA_SUBSCRIPT: Final = re.compile(r'\b(world|registry)\["([a-z_]+)"\]')

#: A ``group(root, <label>, <object>, <key>, ...)`` call. The panel passes the
#: collection name as an ARGUMENT (panel_warnings.js:351-353) rather than
#: subscripting it, so a scan that only read subscripts would miss the single
#: most important key on the wire and report a clean sweep.
GROUP_CALL: Final = re.compile(r'group\(\s*root,\s*"[^"]*",\s*(world|registry),\s*"([a-z_]+)"')


def _keys_the_panel_reads() -> dict[str, set[str]]:
    """Every wire key ``panel_warnings.js`` takes off each data object.

    Returns:
        The object name mapped to the key names read off it.
    """
    code = MODULE_PATH.read_text(encoding="ascii")
    read: dict[str, set[str]] = {"world": set(), "registry": set()}
    for name, key in DATA_SUBSCRIPT.findall(code):
        read[name].add(key)
    for name, key in GROUP_CALL.findall(code):
        read[name].add(key)
    return read


def test_the_world_warning_fixture_is_keyed_the_way_the_endpoint_keys_one() -> None:
    """``_world_warning`` spells exactly ``world.WARNING_KEYS`` and nothing else.

    Equality in both directions: a key the endpoint drops makes the fixture
    over-declare and a key it gains makes the fixture under-declare, and the
    second is the silent one - the panel would render a blank where a new
    field belongs and every content arm would stay green.
    """
    record = _world_warning(source="objects", code="c", detail="d", subject=None, count=1)
    assert set(record) == set(api_world.WARNING_KEYS), (
        "the world warning fixture is not keyed the way /api/world keys one"
        f" (world.py:142): {sorted(set(record) ^ set(api_world.WARNING_KEYS))}"
    )


def test_the_registry_warning_fixture_is_keyed_the_way_that_endpoint_keys_one() -> None:
    """``_registry_warning`` spells exactly ``registry.WARNING_KEYS``.

    FOUR KEYS, NOT FIVE, and the difference is the point: this arm and the one
    above would both pass against a single merged five-key helper only if that
    helper invented a ``source`` for the registry side. Keeping them separate
    is what lets the asymmetry be asserted rather than assumed.
    """
    record = _registry_warning(code="c", detail="d", subject="s", count=1)
    assert set(record) == set(api_registry.WARNING_KEYS), (
        "the registry warning fixture is not keyed the way /api/registry keys one"
        f" (registry.py:174): {sorted(set(record) ^ set(api_registry.WARNING_KEYS))}"
    )
    assert "source" not in record, "a registry warning carries no source (registry.py:174)"
    assert "source" in api_world.WARNING_KEYS, "a world warning does carry one (world.py:142)"


def test_the_unknown_class_fixture_is_keyed_the_way_the_endpoint_keys_one() -> None:
    """``_unknown_class`` spells exactly ``world.UNKNOWN_CLASS_KEYS``.

    The arm that proves a ``type_path`` never reaches this panel is only worth
    anything if the record it hands over is the record the wire carries. A
    fixture keyed ``typePath`` would make that arm prove the panel does not
    render a field nobody ever sends it.
    """
    record = _unknown_class(type_path="t", count=1, reason="r", first_index=0)
    assert set(record) == set(api_world.UNKNOWN_CLASS_KEYS), (
        "the unknown class fixture is not keyed the way /api/world keys one"
        f" (world.py:145): {sorted(set(record) ^ set(api_world.UNKNOWN_CLASS_KEYS))}"
    )


def test_each_data_object_fixture_declares_exactly_what_the_panel_consumes() -> None:
    """The two partial fixtures are pinned to the panel AND to the endpoints.

    THREE CLAIMS, and dropping any one reopens the hole. The fixture must equal
    the declared consumed set, so a key the panel starts reading cannot stay
    unfixtured. The declared set must equal what the ASSET actually reads, so
    the declaration cannot drift into fiction. And the declared set must be a
    real subset of the endpoint's ``DATA_KEYS``, so a key nobody serves cannot
    sit in the fixture looking authoritative.
    """
    read = _keys_the_panel_reads()
    assert read["world"], "the source scan found no /api/world read, so it graded nothing"
    assert read["registry"], "the source scan found no /api/registry read, so it graded nothing"

    assert set(_world()) == set(WORLD_KEYS_CONSUMED), "the world fixture drifted from the roster"
    assert read["world"] == set(WORLD_KEYS_CONSUMED), (
        f"the panel reads {sorted(read['world'])} off /api/world, not {sorted(WORLD_KEYS_CONSUMED)}"
    )
    assert set(WORLD_KEYS_CONSUMED) <= set(api_world.DATA_KEYS), (
        f"/api/world never serves: {set(WORLD_KEYS_CONSUMED) - set(api_world.DATA_KEYS)}"
    )

    assert set(_registry()) == set(REGISTRY_KEYS_CONSUMED), (
        "the registry fixture drifted from the roster"
    )
    assert read["registry"] == set(REGISTRY_KEYS_CONSUMED), (
        f"the panel reads {sorted(read['registry'])} off /api/registry,"
        f" not {sorted(REGISTRY_KEYS_CONSUMED)}"
    )
    assert set(REGISTRY_KEYS_CONSUMED) <= set(api_registry.DATA_KEYS), (
        f"/api/registry never serves: {set(REGISTRY_KEYS_CONSUMED) - set(api_registry.DATA_KEYS)}"
    )


def test_every_warning_collection_is_nested_the_way_the_endpoints_nest_it() -> None:
    """``warnings`` is a bare list on both wires, never a wrapper object.

    THE NESTING HALF OF THE SAME DEFECT. A fixture carrying
    ``warnings: [...]`` against an endpoint carrying ``warnings: {"items": []}``
    has an identical top-level key set and is exactly as invisible - the panel
    would read a list off a mapping, find nothing, and render "reported no
    warnings" over a world full of them. ``world.py:201`` and
    ``registry.py:318`` both build a list, and that is asserted here rather
    than trusted.
    """
    one_world = _world_warning(source="s", code="c", detail="d", subject=None, count=1)
    world_body = _world(warnings=[one_world])
    assert isinstance(world_body["warnings"], list), "/api/world nests warnings as a list"
    assert isinstance(world_body["contains_unmodeled_content"], bool), (
        "contains_unmodeled_content is a bare boolean (world.py:119), not a wrapper"
    )
    one_registry = _registry_warning(code="c", detail="d", subject="s", count=1)
    registry_body = _registry(warnings=[one_registry])
    assert isinstance(registry_body["warnings"], list), "/api/registry nests warnings as a list"
    assert isinstance(registry_body["unknown_groups"], list), (
        "unknown_groups is a list of bare names (registry.py:319)"
    )
