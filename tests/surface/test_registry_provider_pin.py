"""CS-1315: the installed registry is checked against the pinned docs hash on every card.

THE CLAIM. :class:`clockspeed.surface.providers.InstalledRegistryProvider`
builds the registry from the docs file's raw BYTES through
``clockspeed.data.registry.build_registry_from_bytes``, so the registry it
hands up carries the sha256 of the file it was built from; the provider itself
hashes nothing. :class:`clockspeed.surface.providers.StoreAdviceSource` hands
the advisor the pinned docs hash, ``clockspeed.data.version.DOCS_SHA256`` as
it reads at call time, beside the pinned changelist, so over the real route
table:

- a registry built from bytes whose hash differs from the pin serves
  ``registry-mismatch`` on every card, in its reason and its derivation;
- a registry built from bytes equal to the pin serves no registry code - the
  on-pin control;
- a registry with no byte source serves ``registry-unverified`` on every card;
- a build-only difference with equal bytes - the pin's build moved and the
  docs did not, the session 140 case - serves the build's code alone.

THE PIN IS PATCHED, NEVER THE INSTALL'S. Every arm builds from the synthetic
corpus of ``tests/data/synthetic.py`` and sets ``version.DOCS_SHA256`` to that
corpus's own hash, or to an invented digest, through ``monkeypatch``; nothing
here reads a game install or a save. The install is a temporary directory
holding the synthetic bytes at ``version.DOCS_RELATIVE_PARTS``.
"""

from __future__ import annotations

import ast
import dataclasses
import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.data import version
from clockspeed.surface import providers
from clockspeed.surface.api import advice as advice_endpoint
from clockspeed.surface.api import contract, routes
from clockspeed.surface.providers import InstalledRegistryProvider, StoreAdviceSource
from tests.advisor import test_world_advice as world_fixtures
from tests.data import synthetic
from tests.surface import test_map as map_fixtures

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.data.registry import Registry
    from clockspeed.save.world import WorldModel

#: The instant the injected clock answers.
NOW: Final = 1000

#: The synthetic corpus as file bytes, UTF-16 with a byte-order mark.
SYNTHETIC_DOCS: Final = synthetic.DOCS_TEXT.encode("utf-16")

#: The sha256 of those bytes, computed here independently of the data layer.
SYNTHETIC_SHA256: Final = hashlib.sha256(SYNTHETIC_DOCS).hexdigest()

#: An invented pinned docs hash no synthetic bytes produce.
OTHER_SHA256: Final = hashlib.sha256(b"synthetic docs bytes of another build").hexdigest()

#: The two registry codes, spelled here independently of the audit module.
MISMATCH: Final = "registry-mismatch"
UNVERIFIED: Final = "registry-unverified"


def _install(root: Path) -> Path:
    """Lay the synthetic docs bytes out where the provider looks for them."""
    docs = root.joinpath(*version.DOCS_RELATIVE_PARTS)
    docs.parent.mkdir(parents=True)
    docs.write_bytes(SYNTHETIC_DOCS)
    return root


def _installed_registry(root: Path) -> Registry:
    """The registry the provider builds from a synthetic install, read from disk."""
    install = _install(root / "install")
    found = InstalledRegistryProvider(find_install=lambda: (install, "test")).registry()
    assert found is not None
    return found


def _priced_registry(source: Registry) -> Registry:
    """The served world's registry, carrying the provider's provenance verbatim.

    The synthetic corpus prices none of the served world's buildings, so the
    composition suite's registry supplies the figures and the provider-built
    one supplies its source hash - the one field this item adds.
    """
    return dataclasses.replace(
        world_fixtures.synthetic_registry(), source_sha256=source.source_sha256
    )


def _served_texts(directory: Path, model: WorldModel, registry: Registry) -> list[tuple[str, str]]:
    """Each card GET /api/advice serves for a world: its reason, and its derivation."""
    built = routes.build_routes(
        map_fixtures._Worlds(model),  # noqa: SLF001
        map_fixtures._Registries(registry),  # noqa: SLF001
        StoreAdviceSource(directory, clock=lambda: NOW),
    )
    table = {(route.method, route.template): route.handler for route in built}
    cards = _data(table["GET", advice_endpoint.ENDPOINT]({}))["cards"]
    assert isinstance(cards, list)
    texts: list[tuple[str, str]] = []
    for card in cards:
        assert isinstance(card, dict)
        derivation = _data(
            table["GET", advice_endpoint.DERIVATION_ENDPOINT](
                {advice_endpoint.ID_PARAMETER: card["id"]}
            )
        )["derivation"]
        reason = card["reason"]
        assert isinstance(reason, str)
        assert isinstance(derivation, str)
        texts.append((reason, derivation))
    return texts


def _data(response: contract.Response) -> Mapping[str, object]:
    """A 200 response's data object, the contract checked first."""
    assert response.http_status == contract.HTTP_OK
    problems = contract.contract_problems(response)
    count = len(problems)
    assert count == 0, problems
    data = response.payload["data"]
    assert isinstance(data, dict)
    return data


def _naming(texts: list[tuple[str, str]], code: str) -> int:
    """How many served cards name ``code`` in BOTH their reason and their derivation."""
    return sum(1 for reason, derivation in texts if code in reason and code in derivation)


def _mentioning(texts: list[tuple[str, str]], code: str) -> int:
    """How many served cards name ``code`` anywhere."""
    return sum(1 for reason, derivation in texts if code in reason or code in derivation)


# ---------------------------------------------------------------------------
# The provider records provenance and hashes nothing
# ---------------------------------------------------------------------------


def test_the_installed_registry_carries_the_sha256_of_the_docs_bytes(tmp_path: Path) -> None:
    found = _installed_registry(tmp_path)
    assert found.recipes
    assert found.source_sha256 == SYNTHETIC_SHA256


def test_an_injected_byte_reader_is_the_one_the_provider_builds_from(tmp_path: Path) -> None:
    read: list[Path] = []

    def reading(path: Path) -> bytes:
        read.append(path)
        return SYNTHETIC_DOCS

    found = InstalledRegistryProvider(
        find_install=lambda: (tmp_path, "test"), read_docs_bytes=reading
    ).registry()

    assert found is not None
    assert found.source_sha256 == SYNTHETIC_SHA256
    assert read == [tmp_path.joinpath(*version.DOCS_RELATIVE_PARTS)]


def test_a_text_reader_builds_a_registry_with_no_byte_source(tmp_path: Path) -> None:
    """The sibling path: decoded text has no bytes to hash, so it is unverified."""
    found = InstalledRegistryProvider(
        find_install=lambda: (tmp_path, "test"), read_docs=lambda _path: synthetic.DOCS_TEXT
    ).registry()
    assert found is not None
    assert found.recipes
    assert found.source_sha256 is None


@pytest.mark.parametrize("failure", [OSError, ValueError], ids=["os", "value"])
def test_a_byte_reader_that_fails_answers_none(tmp_path: Path, failure: type[Exception]) -> None:
    def refusing(_path: Path) -> bytes:
        raise failure

    provider = InstalledRegistryProvider(
        find_install=lambda: (tmp_path, "test"), read_docs_bytes=refusing
    )
    assert provider.registry() is None


def test_bytes_that_will_not_parse_answer_none(tmp_path: Path) -> None:
    provider = InstalledRegistryProvider(
        find_install=lambda: (tmp_path, "test"),
        read_docs_bytes=lambda _path: b"not a docs document",
    )
    assert provider.registry() is None


# A CODING BUG RAISES; IT NEVER READS AS "NO INSTALL" (CS-1315 fix 1). None is
# the 503 a missing or unreadable install earns. A TypeError is a bug in this
# tree, and folding it into None would serve a confident "no install" for it -
# the silently-wrong answer non-negotiable 7 forbids. Both paths are graded:
# the byte path, and the text path whose catch is b12396c's own.


class _SyntheticCodingBugError(TypeError):
    """A TypeError planted inside the registry build - never a real install fault."""


def _raising_build(*_args: object, **_kwargs: object) -> object:
    raise _SyntheticCodingBugError


@pytest.mark.parametrize("path", ["bytes", "text"])
def test_a_type_error_inside_the_registry_build_propagates_out_of_the_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, path: str
) -> None:
    monkeypatch.setattr(providers.registry, "build_registry", _raising_build)
    if path == "bytes":
        provider = InstalledRegistryProvider(
            find_install=lambda: (tmp_path, "test"), read_docs_bytes=lambda _path: SYNTHETIC_DOCS
        )
    else:
        provider = InstalledRegistryProvider(
            find_install=lambda: (tmp_path, "test"), read_docs=lambda _path: synthetic.DOCS_TEXT
        )

    with pytest.raises(_SyntheticCodingBugError):
        provider.registry()


def test_a_byte_reader_returning_text_raises_and_never_answers_none(tmp_path: Path) -> None:
    """A reader that hands back a str is a bug in its caller, not a missing install."""
    provider = InstalledRegistryProvider(
        find_install=lambda: (tmp_path, "test"),
        read_docs_bytes=lambda _path: synthetic.DOCS_TEXT,  # type: ignore[arg-type,return-value]
    )

    with pytest.raises(TypeError):
        provider.registry()


def test_the_provider_module_hashes_nothing() -> None:
    """The surface passes provenance through; the data layer computes it."""
    source = Path(providers.__file__).read_text(encoding="ascii")
    imported: list[str] = []
    called: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
        elif isinstance(node, ast.Attribute):
            called.append(node.attr)
    assert "hashlib" not in imported
    assert not any(name.startswith("sha") for name in called)
    assert "build_registry_from_bytes" in called


# ---------------------------------------------------------------------------
# Every served card, against the pinned docs hash
# ---------------------------------------------------------------------------


def test_bytes_other_than_the_pin_serve_the_mismatch_on_every_card(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = _priced_registry(_installed_registry(tmp_path))
    monkeypatch.setattr(version, "DOCS_SHA256", OTHER_SHA256)

    texts = _served_texts(tmp_path / "stores", world_fixtures.gap_world(), registry)

    cards = len(texts)
    named = _naming(texts, MISMATCH)
    assert cards > 0
    assert named == cards


def test_bytes_equal_to_the_pin_serve_no_registry_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = _priced_registry(_installed_registry(tmp_path))
    monkeypatch.setattr(version, "DOCS_SHA256", SYNTHETIC_SHA256)

    texts = _served_texts(tmp_path / "stores", world_fixtures.gap_world(), registry)

    cards = len(texts)
    mentioning = _mentioning(texts, MISMATCH) + _mentioning(texts, UNVERIFIED)
    assert cards > 0
    assert mentioning == 0


def test_a_registry_with_no_byte_source_serves_unverified_on_every_card(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(version, "DOCS_SHA256", SYNTHETIC_SHA256)
    # The composition suite stamps its registry verified; this arm strips the
    # stamp, so the registry has no byte source at all.
    unsourced = dataclasses.replace(world_fixtures.synthetic_registry(), source_sha256=None)

    texts = _served_texts(tmp_path, world_fixtures.gap_world(), unsourced)

    cards = len(texts)
    named = _naming(texts, UNVERIFIED)
    mismatch_named = _mentioning(texts, MISMATCH)
    assert cards > 0
    assert named == cards
    assert mismatch_named == 0


def test_a_pin_with_no_docs_hash_serves_unverified_on_every_card(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = _priced_registry(_installed_registry(tmp_path))
    monkeypatch.setattr(version, "DOCS_SHA256", "")

    texts = _served_texts(tmp_path / "stores", world_fixtures.gap_world(), registry)

    cards = len(texts)
    named = _naming(texts, UNVERIFIED)
    assert cards > 0
    assert named == cards


def test_a_build_only_difference_with_equal_bytes_serves_the_build_code_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The pin's build moved and its docs bytes did not: the session 140 patch.

    The save was written by the old pinned build, so every card names the
    build mismatch; the registry's bytes equal the pin's, so none names a
    registry code, and nothing reads the install's build at all.
    """
    model = world_fixtures.gap_world()
    registry = _priced_registry(_installed_registry(tmp_path))
    pin = version.GAME_CHANGELIST
    assert pin is not None
    monkeypatch.setattr(version, "GAME_CHANGELIST", pin + 1)
    monkeypatch.setattr(version, "DOCS_SHA256", SYNTHETIC_SHA256)

    texts = _served_texts(tmp_path / "stores", model, registry)

    cards = len(texts)
    build_named = _naming(texts, "build-mismatch")
    registry_named = _mentioning(texts, MISMATCH) + _mentioning(texts, UNVERIFIED)
    assert cards > 0
    assert build_named == cards
    assert registry_named == 0


def test_the_docs_pin_is_read_at_call_time(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """One source, two pins in turn: the second call reads the second pin."""
    registry = _priced_registry(_installed_registry(tmp_path))
    source = StoreAdviceSource(tmp_path / "stores", clock=lambda: NOW)
    world = world_fixtures.gap_world()

    monkeypatch.setattr(version, "DOCS_SHA256", SYNTHETIC_SHA256)
    before = source.advice(world, registry)
    monkeypatch.setattr(version, "DOCS_SHA256", OTHER_SHA256)
    after = source.advice(world, registry)

    assert before is not None
    assert after is not None
    clean = sum(1 for a in before.cards if MISMATCH in a.card.tier2)
    named = sum(1 for a in after.cards if MISMATCH in a.card.tier2)
    assert len(after.cards) > 0
    assert clean == 0
    assert named == len(after.cards)
