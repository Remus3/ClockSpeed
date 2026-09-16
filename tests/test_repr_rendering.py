"""CS-852 - the repr channel, graded on what a GENERATED repr actually prints.

WHAT IS ASSERTED HERE AND WHAT IS NOT. The subject is the ``__repr__`` a shipped
class renders when nobody wrote one - the channel ``tests/
repr_rendering_guard.py`` derives statically from the field annotations, and
which the forced arms below measure for real by constructing the shipped types
with a planted marker and grepping the rendering for it. The ASSERTED
EXPRESSION belongs to CS-850 and the frame LOCALS belong to CS-851; a
hand-written repr's per-field decision over a plain ``str`` belongs to CS-850
too, and this module deliberately does not re-grade it.

THE ARMS DO NOT DERIVE FROM THE FINDINGS. Every synthetic case below is authored
in this file and parsed on the spot; not one reads :func:`scan_tree` to decide
what to test. Three items were refuted in one session for proofs whose cases
came from the live population, so REPAIRING A LEAK TURNED THE PROOF RED and a
green run certified that the tree still leaked.
``test_a_corpus_with_no_carrier_yields_no_finding`` proves the
green-on-a-clean-tree property directly.

THE RUNTIME ARM IS DERIVED, NOT LISTED, AND THE COVERAGE IS ASSERTED. Building
an instance needs per-type constructor knowledge that no annotation carries, so
:data:`FORCED` is written by hand - and
``test_every_carrier_in_the_population_is_forced`` fails if the derivation ever
holds a carrier class ``FORCED`` does not construct. The hand-written half
cannot silently fall behind the derived half.

THE POPULATION IS ASSERTED NON-EMPTY. An equality over nothing is satisfied for
free, and this project has shipped that mistake in two consecutive sessions -
see ``memory/an-empty-population-satisfies-every-zero.md``.
"""

from __future__ import annotations

import ast
import re
import warnings
from dataclasses import fields, is_dataclass
from functools import partial
from pathlib import Path
from typing import Final

import pytest
from _pytest._io.saferepr import saferepr

from clockspeed.data.assets import ExtractResult
from clockspeed.save.chunks import DecompressedBody
from clockspeed.save.header import _Cursor as HeaderCursor
from clockspeed.save.objects import _Cursor as ObjectCursor
from clockspeed.save.usmap import _Reader as UsmapReader
from clockspeed.save.workdir import ForbiddenRoot, SaveListing
from clockspeed.surface.config import ServerConfig
from clockspeed.surface.providers import (
    InstalledRegistryProvider,
    SaveWorldProvider,
    StaticAssets,
)
from tests.repr_rendering_guard import (
    ALTERNATE_RENDERING_METHODS,
    CARRIER_TYPES,
    EXEMPT,
    KIND_DISCLOSED,
    KIND_GENERATED,
    KIND_INHERITED,
    KIND_WITHHELD,
    LEAKING_KINDS,
    REPO_ROOT,
    SAVE_LAYER,
    ReprCandidate,
    alternate_rendering_methods,
    candidates_in,
    describe,
    exception_rendering_classes,
    opaque_class_names,
    scan_tree,
    stale_exemptions,
    swept_modules,
)

#: A module path inside the graded layer, so R1 fires on a synthetic corpus.
#: No file of this name exists - the derivation reads a parsed tree, not a disk.
SYNTHETIC_MODULE: Final = f"{SAVE_LAYER}synthetic_corpus.py"

#: Planted into a real save-carrying field and grepped for in the rendering.
#: Obviously synthetic: this is never a real token, path or account id.
MARKER: Final = "PLANTED_CS852_MARKER_zzz"

#: Shortest string that can carry a real, measured reason rather than a stamp.
MINIMUM_REASON_CHARS: Final = 40

#: Underscore-carrying words that are PROSE in an exemption reason rather than
#: a citation. Kept short and explicit: every addition widens the hole that the
#: identifier check exists to close, so a new entry should be a real English
#: compound and not a convenient way to silence a bad citation.
_REASON_PROSE: frozenset[str] = frozenset({"f_string", "non_negotiables"})

#: Save-layer error classes that render through ``BaseException`` - a channel
#: ``tests/repr_rendering_guard.py`` provably does NOT grade. Derived once from
#: :func:`exception_rendering_classes` and recorded here so the set is asserted
#: in BOTH directions; see
#: ``test_the_exception_rendering_channel_is_recorded_not_silently_ungraded``.
#:
#: THIS IS A GAP, NOT A CLEARANCE. Their real protection today is the
#: hand-placed ``locate.redact`` calls at the raise sites and the
#: ``_checked_field`` validation some of them apply - neither of which this
#: module reads. Closing it needs the message-building code path, which is why
#: CS-852 stays open.
UNGRADED_EXCEPTION_CHANNEL: tuple[str, ...] = (
    "clockspeed/save/chunks.py::ChunkBudgetExceededError",
    "clockspeed/save/chunks.py::ChunkDecompressError",
    "clockspeed/save/chunks.py::ChunkError",
    "clockspeed/save/chunks.py::ChunkFramingError",
    "clockspeed/save/chunks.py::ChunkTruncatedError",
    "clockspeed/save/header.py::HeaderError",
    "clockspeed/save/header.py::HeaderFormatError",
    "clockspeed/save/header.py::HeaderReadError",
    "clockspeed/save/header.py::HeaderTruncatedError",
    "clockspeed/save/header.py::PersonalDataOptInRequiredError",
    "clockspeed/save/header.py::UnsupportedHeaderVersionError",
    "clockspeed/save/objects.py::ObjectBudgetExceededError",
    "clockspeed/save/objects.py::ObjectError",
    "clockspeed/save/objects.py::ObjectFormatError",
    "clockspeed/save/objects.py::ObjectTruncatedError",
    "clockspeed/save/objects.py::UnsupportedBodyLayoutError",
    "clockspeed/save/objects.py::UnsupportedSaveVersionError",
    "clockspeed/save/usmap.py::UnsupportedUsmapCompressionError",
    "clockspeed/save/usmap.py::UsmapError",
    "clockspeed/save/usmap.py::UsmapFormatError",
    "clockspeed/save/workdir.py::DestinationRefusedError",
    "clockspeed/save/workdir.py::SourceUnreadableError",
    "clockspeed/save/workdir.py::WorkDirError",
    "clockspeed/save/world.py::WorldLoadError",
)

#: Every class the derivation currently puts in the population, recorded so
#: membership is asserted in BOTH directions rather than for the fourteen keys
#: two other arms happen to name.
#:
#: PINNING THIS IS NOT ANTI-MONOTONE. Repairing a class does not remove it -
#: a redacted carrier is still a carrier, and a repaired class stays in the
#: population with kind ``withheld``. What the record catches is a member
#: LEAVING silently, which an adversary produced by widening
#: ``opaque_class_names``: the population went 43 to 42, one save-layer class
#: dropped out of grading, and every arm stayed green.
RECORDED_POPULATION: tuple[str, ...] = (
    "clockspeed/data/assets.py::ExtractResult",
    "clockspeed/save/chunks.py::ChunkError",
    "clockspeed/save/chunks.py::ChunkFrame",
    "clockspeed/save/chunks.py::ChunkWarning",
    "clockspeed/save/chunks.py::DecompressedBody",
    "clockspeed/save/header.py::HeaderFormatError",
    "clockspeed/save/header.py::HeaderReadError",
    "clockspeed/save/header.py::HeaderStrings",
    "clockspeed/save/header.py::HeaderTruncatedError",
    "clockspeed/save/header.py::HeaderWarning",
    "clockspeed/save/header.py::SaveHeader",
    "clockspeed/save/header.py::_Cursor",
    "clockspeed/save/objects.py::BodyLayout",
    "clockspeed/save/objects.py::Collectable",
    "clockspeed/save/objects.py::ContainerElement",
    "clockspeed/save/objects.py::ContainerValue",
    "clockspeed/save/objects.py::ItemListEntry",
    "clockspeed/save/objects.py::ObjectError",
    "clockspeed/save/objects.py::ObjectRecord",
    "clockspeed/save/objects.py::ObjectReference",
    "clockspeed/save/objects.py::ObjectTable",
    "clockspeed/save/objects.py::ObjectWarning",
    "clockspeed/save/objects.py::PropertyResult",
    "clockspeed/save/objects.py::RecordIndex",
    "clockspeed/save/objects.py::ReferenceResolution",
    "clockspeed/save/objects.py::StructValue",
    "clockspeed/save/objects.py::UnknownClass",
    "clockspeed/save/objects.py::_Cursor",
    "clockspeed/save/objects.py::_PayloadWalk",
    "clockspeed/save/objects.py::_UnknownLog",
    "clockspeed/save/usmap.py::PropertyEntry",
    "clockspeed/save/usmap.py::PropertyMap",
    "clockspeed/save/usmap.py::Schema",
    "clockspeed/save/usmap.py::UsmapFormatError",
    "clockspeed/save/usmap.py::UsmapWarning",
    "clockspeed/save/usmap.py::_NameTable",
    "clockspeed/save/usmap.py::_Reader",
    "clockspeed/save/usmap.py::_WarningLog",
    "clockspeed/save/workdir.py::ForbiddenRoot",
    "clockspeed/save/workdir.py::ListingProblem",
    "clockspeed/save/workdir.py::SaveListing",
    "clockspeed/save/world.py::ContainerContents",
    "clockspeed/save/world.py::ContainerEntry",
    "clockspeed/save/world.py::RecordProperties",
    "clockspeed/save/world.py::ResourceNode",
    "clockspeed/save/world.py::UnlockState",
    "clockspeed/save/world.py::WorldLoadError",
    "clockspeed/save/world.py::WorldModel",
    "clockspeed/save/world.py::WorldWarning",
    "clockspeed/surface/config.py::ServerConfig",
    "clockspeed/surface/providers.py::InstalledRegistryProvider",
    "clockspeed/surface/providers.py::SaveWorldProvider",
    "clockspeed/surface/providers.py::StaticAssets",
)


def _findings(source: str) -> list[ReprCandidate]:
    """Every finding the derivation reports for one synthetic module.

    Args:
        source: The module text.

    Returns:
        The leaking, unexempted candidates.
    """
    tree = ast.parse(source)
    found = candidates_in(SYNTHETIC_MODULE, tree, opaque_class_names())
    return [c for c in found if c.kind in LEAKING_KINDS and c.key not in EXEMPT]


def _kinds(source: str) -> dict[str, str]:
    """Each class in a synthetic module to the kind the derivation gave it.

    Args:
        source: The module text.

    Returns:
        Class name to kind.
    """
    tree = ast.parse(source)
    return {
        c.class_name: c.kind for c in candidates_in(SYNTHETIC_MODULE, tree, opaque_class_names())
    }


# ---------------------------------------------------------------------------
# The derivation, graded on corpora authored here
# ---------------------------------------------------------------------------


def test_a_planted_dataclass_carrying_bytes_is_a_finding() -> None:
    """The acceptance's required proof: a new unredacted carrier turns it RED."""
    source = (
        "from dataclasses import dataclass\n"
        "@dataclass(frozen=True)\n"
        "class Planted:\n"
        "    payload: bytes\n"
        "    count: int\n"
    )
    found = _findings(source)
    names = sorted(c.class_name for c in found)
    assert names == ["Planted"], f"expected the planted carrier to be a finding, got {names}"
    assert found[0].kind == KIND_GENERATED


def test_a_planted_dataclass_carrying_a_path_is_a_finding() -> None:
    """A home path is a carrier too - non-negotiable 3, no save needed."""
    source = (
        "from dataclasses import dataclass\n"
        "from pathlib import Path\n"
        "@dataclass(frozen=True)\n"
        "class Planted:\n"
        "    where: Path\n"
    )
    names = sorted(c.class_name for c in _findings(source))
    assert names == ["Planted"], f"expected the planted path carrier to be a finding, got {names}"


def test_a_planted_namedtuple_carrying_bytes_is_a_finding() -> None:
    """A NamedTuple generates a field-rendering repr the same way a dataclass does."""
    source = "from typing import NamedTuple\nclass Planted(NamedTuple):\n    payload: bytes\n"
    names = sorted(c.class_name for c in _findings(source))
    assert names == ["Planted"], f"expected the planted NamedTuple to be a finding, got {names}"


def test_a_plain_class_carrying_bytes_is_not_a_finding() -> None:
    """THE MEASURED DISCRIMINATOR, pinned so it cannot be simplified away.

    ``object.__repr__`` renders ``<module.Class object at 0x...>`` and discloses
    no field. Grading on "ships no ``__repr__``" instead of on "gets a GENERATED
    one" reported both shipped ``_Cursor`` types - each holding a raw save
    buffer - as leaks, which is a false positive that would have buried the
    three real findings.
    """
    source = (
        "class Planted:\n    def __init__(self, data: bytes) -> None:\n        self._data = data\n"
    )
    assert _findings(source) == []
    assert _kinds(source).get("Planted") == KIND_INHERITED


def test_a_repr_false_class_with_a_withholding_repr_is_not_a_finding() -> None:
    """The remedy actually clears the finding."""
    source = (
        "from dataclasses import dataclass\n"
        "@dataclass(frozen=True, repr=False)\n"
        "class Planted:\n"
        "    payload: bytes\n"
        "    count: int\n"
        "    def __repr__(self) -> str:\n"
        "        return f'{type(self).__name__}(count={self.count})'\n"
    )
    assert _findings(source) == []


def test_a_repr_false_class_that_renders_the_carrier_anyway_is_a_finding() -> None:
    """THE BYPASS IS CLOSED.

    Without this arm the remedy for every finding would be to write a
    ``__repr__`` that changes nothing, and the guard would grade the DECORATOR
    rather than the rendering.
    """
    source = (
        "from dataclasses import dataclass\n"
        "@dataclass(frozen=True, repr=False)\n"
        "class Planted:\n"
        "    payload: bytes\n"
        "    def __repr__(self) -> str:\n"
        "        return f'{type(self).__name__}(payload={self.payload!r})'\n"
    )
    found = _findings(source)
    names = sorted(c.class_name for c in found)
    assert names == ["Planted"], f"expected the rendering repr to be a finding, got {names}"
    assert found[0].kind == KIND_DISCLOSED


def test_a_masked_carrier_is_not_a_finding() -> None:
    """A reduction over the carrier discloses nothing, so it must not be flagged."""
    source = (
        "from dataclasses import dataclass\n"
        "@dataclass(frozen=True, repr=False)\n"
        "class Planted:\n"
        "    payload: bytes\n"
        "    def __repr__(self) -> str:\n"
        "        return f'{type(self).__name__}(bytes={len(self.payload)})'\n"
    )
    assert _findings(source) == []


def test_a_corpus_with_no_carrier_yields_no_finding() -> None:
    """GREEN ON A CLEAN TREE, proven directly rather than inferred.

    A check that can only be green while the defect exists is worthless, and
    three items were refuted in one session for exactly that shape.
    """
    source = (
        "from dataclasses import dataclass\n"
        "@dataclass(frozen=True)\n"
        "class Counts:\n"
        "    total: int\n"
        "    ratio: float\n"
        "class Reader:\n"
        "    def __init__(self, data: bytes) -> None:\n"
        "        self._data = data\n"
    )
    assert _findings(source) == []


def test_a_carrier_above_the_save_layer_is_a_finding() -> None:
    """R2 GRADED ON ITS OWN, and it was untested until this arm existed.

    Every other synthetic corpus here is parsed under :data:`SYNTHETIC_MODULE`,
    which sits INSIDE the save layer, so R1 catches a carrier there whatever R2
    does. Deleting R2 outright therefore left the whole suite green - the rule
    that exists to catch a save value cached in ``advisor/`` or ``surface/``
    was load-bearing for nothing a test could see.
    """
    source = (
        "from dataclasses import dataclass\n"
        "@dataclass(frozen=True)\n"
        "class Cached:\n"
        "    payload: bytes\n"
    )
    found = candidates_in("clockspeed/advisor/cards.py", ast.parse(source), opaque_class_names())
    leaking = [c for c in found if c.kind in LEAKING_KINDS and c.key not in EXEMPT]
    names = sorted(c.class_name for c in leaking)
    assert names == ["Cached"], f"R2 did not catch a carrier above the save layer, got {names}"
    assert leaking[0].rule == "R2"


def test_a_plain_string_above_the_save_layer_is_not_a_finding() -> None:
    """R2 MUST NOT OVER-REACH.

    R1's wider net is scoped to the save layer on purpose. If R2 fired on a
    bare ``str`` it would grade every dataclass in ``solve/`` and ``data/``,
    whose fields hold recipe keys and registry content - game data, not
    personal data - and the exemption record would become a rubber stamp with
    dozens of entries.
    """
    source = (
        "from dataclasses import dataclass\n@dataclass(frozen=True)\nclass Note:\n    label: str\n"
    )
    found = candidates_in("clockspeed/solve/ratio.py", ast.parse(source), opaque_class_names())
    assert found == [], f"R2 over-reached onto a plain str above the save layer: {found}"


def test_no_shipped_class_renders_through_an_ungraded_channel() -> None:
    """NO SILENT CAP: ``__str__`` and ``__format__`` are NOT graded here.

    ``f"{obj}"`` calls ``__str__`` and falls back to ``__repr__`` only while no
    ``__str__`` exists. Measured today: the shipped tree defines neither. This
    arm fails the day one arrives, so the decision to cover it is taken
    deliberately instead of the guard quietly grading less than it appears to.
    """
    defined = alternate_rendering_methods()
    assert defined == (), (
        "a shipped class now defines __str__ or __format__, a rendering channel "
        f"this guard does not grade: {list(defined)}. Either withhold there too "
        "or widen this module deliberately."
    )


# ---------------------------------------------------------------------------
# The live tree
# ---------------------------------------------------------------------------


def test_the_population_is_not_empty() -> None:
    """An equality over an empty population is satisfied for free."""
    population, _ = scan_tree()
    assert population, "the derivation found NO classes at all - it is not grading anything"
    graded = [c for c in population if c.kind in LEAKING_KINDS or c.kind == KIND_WITHHELD]
    assert graded, "no class in the population renders or withholds a field - derivation is blind"


def test_the_population_holds_the_shipped_carriers() -> None:
    """The three known carrier types are IN the population, whatever their grade.

    Membership survives the repair - a redacted carrier is still a carrier - so
    this arm is not anti-monotone.
    """
    population, _ = scan_tree()
    carriers = {c.key for c in population if c.carriers}
    for expected in (
        "clockspeed/save/chunks.py::DecompressedBody",
        "clockspeed/save/workdir.py::SaveListing",
        "clockspeed/save/workdir.py::ForbiddenRoot",
    ):
        assert expected in carriers, f"{expected} left the population - the derivation went blind"


def test_the_sweep_reaches_beyond_the_save_layer() -> None:
    """SHIPPED_ROOT's REACH IS GRADED, not merely its rule.

    Every candidate in this tree happens to live under the save layer, so an
    adversary narrowed ``SHIPPED_ROOT`` back to ``clockspeed/save/`` and no arm
    went red: R2, whose whole purpose is catching a save value cached above the
    save layer, could be switched off in silence.
    """
    swept = swept_modules()
    assert swept, "the sweep walks no modules at all"
    above = [m for m in swept if not m.startswith(SAVE_LAYER)]
    assert above, (
        "the sweep reaches no module above the save layer, so R2 grades "
        f"nothing it was written for; walked {len(swept)} module(s)"
    )


def test_the_exception_rendering_channel_is_recorded_not_silently_ungraded() -> None:
    """NO SILENT CAP over the channel this module provably does NOT grade.

    ``BaseException.__repr__`` is not ``object.__repr__``: it renders ``args``,
    and ``__str__`` renders it too. So the :data:`KIND_INHERITED` premise -
    that a class with no ``__repr__`` discloses no field - is true for a plain
    class and false for every exception. Deciding whether one leaks needs the
    message-building code path rather than the field annotations this module
    reads, so the population is RECORDED here instead of graded.

    The record is asserted in BOTH directions. A new save-layer error reddens
    this arm and forces the decision; a deleted one reddens it too, so the
    record cannot rot into a list of names that no longer mean anything.
    """
    recorded = set(UNGRADED_EXCEPTION_CHANNEL)
    live = set(exception_rendering_classes())
    assert live, "the exception census found nothing - it is not measuring"
    arrived = sorted(live - recorded)
    departed = sorted(recorded - live)
    assert arrived == [], (
        "save-layer error class(es) arrived on a rendering channel this guard "
        f"does not grade, and are unrecorded: {arrived}"
    )
    assert departed == [], f"recorded error class(es) no longer exist; delete them: {departed}"


def test_no_shipped_class_renders_a_graded_field() -> None:
    """THE CONTRACT. Every population member withholds, or states an exemption."""
    _, findings = scan_tree()
    count = len(findings)
    assert count == 0, f"{count} shipped class(es) render a graded field:\n{describe(findings)}"


def test_every_exemption_names_a_class_the_derivation_found() -> None:
    """An exemption for a class that does not exist grades nothing."""
    population, _ = scan_tree()
    known = {c.key for c in population}
    unknown = sorted(set(EXEMPT) - known)
    assert unknown == [], f"exemption(s) naming no class in the population: {unknown}"


def test_every_exemption_states_a_reason() -> None:
    """A blank reason is a rubber stamp with a key on it."""
    thin = sorted(
        key for key, reason in EXEMPT.items() if len(reason.strip()) < MINIMUM_REASON_CHARS
    )
    assert thin == [], f"exemption(s) with no stated reason: {thin}"


def test_every_identifier_an_exemption_cites_exists_in_the_module_it_names() -> None:
    """A REASON MAY NOT CITE CODE THAT DOES NOT EXIST.

    The length check above is satisfied by forty spaces. An adversary replaced
    all eleven reasons with forty literal characters and every arm stayed
    green, which is what let a reason ship citing ``_warn`` - a function that
    has never existed in this repository, transcribed from a sibling module's
    ``_warning``. The conclusion happened to be right and the evidence was
    invented.

    Only tokens carrying an underscore are checked. That is what separates an
    identifier from an English word without needing a list of English words,
    and it is the class the fabricated citation belonged to.
    """
    identifier = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
    missing: list[str] = []
    for key, reason in EXEMPT.items():
        module = key.split("::", 1)[0]
        source = (REPO_ROOT / module).read_text(encoding="utf-8")
        for token in identifier.findall(reason):
            if "_" not in token or token in _REASON_PROSE:
                continue
            if token not in source:
                missing.append(f"{key} cites {token!r}, absent from {module}")
    assert missing == [], "exemption(s) citing code that does not exist:\n" + "\n".join(missing)


def test_a_repaired_exemption_is_reported_rather_than_reddening() -> None:
    """BOTH DIRECTIONS, and this one WARNS.

    Failing here would need every exempted class to still be leaking, which is
    the anti-monotone shape: repairing one would turn the proof red.
    """
    fabricated = {"clockspeed/save/nowhere.py::NoSuchClass": "a key naming nothing"}
    reported = stale_exemptions(fabricated)
    assert reported == ("clockspeed/save/nowhere.py::NoSuchClass",), (
        "the stale-exemption reporter does not report a key that names no "
        f"candidate, so its clean result on the live record proves nothing: {reported}"
    )
    assert stale_exemptions({}) == (), "an empty record cannot be stale"

    stale = stale_exemptions()
    if stale:
        lines = "\n".join(f"  stale EXEMPT key, remove it: {key!r}" for key in stale)
        warnings.warn(
            f"{len(stale)} exemption(s) no longer needed:\n{lines}",
            stacklevel=1,
        )


# ---------------------------------------------------------------------------
# Forced rendering - what the interpreter actually prints
# ---------------------------------------------------------------------------


def _install_under(root: Path) -> tuple[Path | None, str]:
    """Stand in for the install resolver, so a bound Path reaches a repr.

    A ``functools.partial`` over this renders its BOUND ARGUMENT in its own
    repr, which is what lets :data:`FORCED` plant the marker in a class whose
    every field is a callable. ``InstalledRegistryProvider`` is that class:
    both its fields are ``Callable``, and ``_find_install`` is graded a
    carrier because ``Path`` appears in the RETURN half of its annotation.
    An anonymous lambda there renders nothing, which would make
    ``test_a_forced_subject_actually_carries_the_marker`` fail rather than
    pass vacuously - MEASURED both ways before this helper was written.

    Args:
        root: The install directory to answer with.

    Returns:
        The pair ``locate.resolve_game_dir`` returns.
    """
    return (root, "test")


#: Every carrier-holding class in the population, built with a planted marker.
#: Hand-written because a constructor signature is not in an annotation, and
#: cross-checked against the derivation by the coverage arm below.
#:
#: THE THREE PLAIN READERS ARE HERE ON PURPOSE. Each holds a raw save or install
#: buffer in ``_data`` and each is graded ``inherited`` - safe - by the static
#: derivation. Forcing them makes that a MEASURED fact at runtime rather than a
#: prediction from the AST, and it is the arm that would go red if a later edit
#: turned one of them into a dataclass. The coverage arm below is what put them
#: in this record: the first draft listed only the three dataclasses and was
#: told it had missed three carriers.
FORCED: Final[dict[str, object]] = {
    "clockspeed/data/assets.py::ExtractResult": ExtractResult(
        index=None, artifact=Path(f"C:/Users/{MARKER}/header_index.json"), reason=""
    ),
    "clockspeed/save/chunks.py::DecompressedBody": DecompressedBody(
        payload=MARKER.encode("ascii"), chunk_count=1
    ),
    "clockspeed/save/workdir.py::SaveListing": SaveListing(
        saves=(Path(f"C:/Users/{MARKER}/world.sav"),), problems=()
    ),
    "clockspeed/save/workdir.py::ForbiddenRoot": ForbiddenRoot(
        label="the game install", resolved=Path(f"C:/Users/{MARKER}/game")
    ),
    "clockspeed/save/header.py::_Cursor": HeaderCursor(MARKER.encode("ascii")),
    "clockspeed/save/objects.py::_Cursor": ObjectCursor(MARKER.encode("ascii")),
    "clockspeed/save/usmap.py::_Reader": UsmapReader(MARKER.encode("ascii")),
    "clockspeed/surface/config.py::ServerConfig": ServerConfig(
        host="127.0.0.1",
        port=0,
        cert_path=Path(f"C:/Users/{MARKER}/dashboard.cert.pem"),
        key_path=Path(f"C:/Users/{MARKER}/dashboard.key.pem"),
        web_dir=Path(f"C:/Users/{MARKER}/web"),
    ),
    "clockspeed/surface/providers.py::SaveWorldProvider": SaveWorldProvider(
        Path(f"C:/Users/{MARKER}/account")
    ),
    "clockspeed/surface/providers.py::InstalledRegistryProvider": InstalledRegistryProvider(
        find_install=partial(_install_under, Path(f"C:/Users/{MARKER}/game"))
    ),
    "clockspeed/surface/providers.py::StaticAssets": StaticAssets(
        Path(f"C:/Users/{MARKER}/web"), ("app.js",)
    ),
}


def test_every_carrier_in_the_population_is_forced() -> None:
    """The hand-written half cannot fall behind the derived half."""
    population, _ = scan_tree()
    derived = {c.key for c in population if c.carriers}
    missing = sorted(derived - set(FORCED))
    assert missing == [], f"carrier class(es) the forced arm never constructs: {missing}"


@pytest.mark.parametrize("key", sorted(FORCED))
def test_a_forced_subject_actually_carries_the_marker(key: str) -> None:
    """THE POSITIVE CONTROL, and without it the arm below proves nothing.

    ``assert MARKER not in rendered`` passes when the repr withholds AND when
    the marker was never planted - byte-identical outcomes. An adversary
    emptied one FORCED payload to ``b""`` and the suite stayed green while a
    genuinely leaking repr rendered a real type path and session name.

    The marker is looked for in the FIELD VALUES rather than in the object's
    repr, because the object's repr is the very thing under test.
    """
    subject = FORCED[key]
    if is_dataclass(subject):
        values = [getattr(subject, f.name) for f in fields(subject)]
    else:
        values = list(vars(subject).values())
    carrying = [v for v in values if MARKER in repr(v)]
    assert carrying, (
        f"{key} was constructed without the planted marker in any field, so "
        "the withholding arm for it is vacuous"
    )


@pytest.mark.parametrize("key", sorted(FORCED))
def test_a_forced_rendering_holds_no_planted_marker(key: str) -> None:
    """WHAT THE INTERPRETER PRINTS, not what the AST predicts.

    The static derivation and this arm are independent readings of the same
    property. Agreement between them is the evidence; either alone is a claim.
    """
    subject = FORCED[key]
    direct = repr(subject)
    safe = saferepr(subject)
    assert MARKER not in direct, f"{key} renders the planted marker through repr()"
    assert MARKER not in safe, f"{key} renders the planted marker through pytest saferepr"


@pytest.mark.parametrize("key", sorted(FORCED))
def test_a_forced_rendering_still_names_its_type(key: str) -> None:
    """Withholding must not collapse into a rendering that says nothing."""
    short = key.rsplit("::", 1)[1]
    rendered = repr(FORCED[key])
    assert short in rendered, f"{key} no longer names its own type"
    assert rendered != f"{short}()", (
        f"{key} collapsed to a bare type name, which withholds by saying "
        "nothing at all - an adversary made this pass by returning exactly that"
    )


def test_the_population_membership_is_pinned_in_both_directions() -> None:
    """A MEMBER MAY NOT LEAVE THE POPULATION SILENTLY.

    ``test_the_population_is_not_empty`` pins only non-emptiness and two other
    arms pin fourteen keys between them, so an adversary widened
    ``opaque_class_names`` until one save-layer class was graded
    non-disclosing, watched the population fall from 43 to 42, and every arm
    stayed green. Twenty-nine members could leave one at a time undetected.
    """
    population, _ = scan_tree()
    live = {c.key for c in population}
    recorded = set(RECORDED_POPULATION)
    departed = sorted(recorded - live)
    arrived = sorted(live - recorded)
    assert departed == [], (
        "class(es) left the graded population without the record being "
        f"updated, so they are no longer graded by anything: {departed}"
    )
    assert arrived == [], (
        "new class(es) entered the graded population; confirm each is either "
        f"withholding or exempt, then record them: {arrived}"
    )


def test_the_alternate_rendering_vocabulary_is_not_empty() -> None:
    """An emptied vocabulary makes the ungraded-channel census silently clean.

    The census reports ``()`` both when no shipped class defines one of these
    methods AND when it is looking for nothing at all. An adversary proved the
    two are not equivalent by pairing: planting a ``__str__`` reddens the arm
    on a pristine tree and passes once the vocabulary is emptied.
    """
    assert ALTERNATE_RENDERING_METHODS, "the census searches for no method at all"
    assert "__str__" in ALTERNATE_RENDERING_METHODS
    assert "__format__" in ALTERNATE_RENDERING_METHODS


def test_the_carrier_vocabulary_is_not_empty() -> None:
    """A carrier set emptied by an edit would make every arm above vacuous."""
    assert CARRIER_TYPES, "CARRIER_TYPES is empty - R2 grades nothing"
    assert "bytes" in CARRIER_TYPES
    assert "Path" in CARRIER_TYPES
