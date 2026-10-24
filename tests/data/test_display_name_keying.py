"""CS-1240: renaming every display name in the docs changes nothing the registry joins.

THE CLAIM (CS-1240 acceptance 2, at the data layer). ``build_registry`` keys
every namespace by ``ClassName`` and joins every recipe, produced-in token,
fuel and resource reference by it, so the same synthetic docs corpus with every
non-empty ``mDisplayName`` changed builds a registry that differs ONLY in those
display names: the same keys, the same figures, the same flagged-and-skipped
warnings, the same unknown groups and the same declared classes. A join keyed
on a display name would move a key, drop an entry or add a warning here.

The control proves the rename really reached the built registry, so the
equality half is not satisfied by a corpus that carried no display name.

Both corpora are ``tests.data.synthetic``'s hand-authored ones; nothing is cut
from a real docs file.
"""

from __future__ import annotations

from dataclasses import fields, replace
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final

import pytest

from clockspeed.data.registry import Registry, build_registry
from tests.data import synthetic

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

#: What every non-empty display name is renamed to: a prefix, so the new name
#: is printable ASCII and differs from the old one.
RENAME_PREFIX: Final = "Renamed "

#: The two hand-authored corpora, each as a fresh mutable group list.
CORPORA: Final[dict[str, Callable[[], list[Any]]]] = {
    "registry": synthetic.docs_json,
    "fuel": synthetic.fuel_groups,
}


def _rename_groups(groups: list[Any]) -> int:
    """Rename every non-empty ``mDisplayName`` in place.

    Args:
        groups: A top-level group list.

    Returns:
        How many display names were renamed.
    """
    renamed = 0
    for group in groups:
        classes = group.get(synthetic.KEY_CLASSES) if isinstance(group, dict) else None
        for entry in classes if isinstance(classes, list) else ():
            current = entry.get(synthetic.KEY_DISPLAY_NAME) if isinstance(entry, dict) else None
            if isinstance(current, str) and current:
                entry[synthetic.KEY_DISPLAY_NAME] = RENAME_PREFIX + current
                renamed += 1
    return renamed


def _nameless(entries: Mapping[str, Any]) -> Mapping[str, Any]:
    """One namespace with every display name blanked, for an equality.

    Args:
        entries: A registry namespace.

    Returns:
        A read-only copy whose entries carry an empty display name.
    """
    out: dict[str, Any] = {}
    for key, entry in entries.items():
        names = {field.name for field in fields(entry)}
        out[key] = replace(entry, display_name="") if "display_name" in names else entry
    return MappingProxyType(out)


def nameless(registry: Registry) -> Registry:
    """The registry with every display name blanked and nothing else touched.

    Args:
        registry: The registry.

    Returns:
        The blanked registry.
    """
    return replace(
        registry,
        items=_nameless(registry.items),
        recipes=_nameless(registry.recipes),
        buildings=_nameless(registry.buildings),
        extractors=_nameless(registry.extractors),
        generators=_nameless(registry.generators),
    )


def _display_names(registry: Registry) -> tuple[str, ...]:
    """Every display name the registry carries, in namespace and key order.

    Args:
        registry: The registry.

    Returns:
        The names.
    """
    namespaces = (
        registry.items,
        registry.recipes,
        registry.buildings,
        registry.extractors,
        registry.generators,
    )
    return tuple(
        str(getattr(namespace[key], "display_name", ""))
        for namespace in namespaces
        for key in sorted(namespace)
    )


def _built(corpus: str, *, rename: bool) -> tuple[Registry, int]:
    """Build one corpus, renamed or not.

    Args:
        corpus: A key of :data:`CORPORA`.
        rename: Whether to rename every display name first.

    Returns:
        The registry, and how many display names were renamed.
    """
    groups = CORPORA[corpus]()
    renamed = _rename_groups(groups) if rename else 0
    return build_registry(synthetic.document_from(groups)), renamed


@pytest.mark.parametrize("corpus", sorted(CORPORA))
def test_a_display_name_change_changes_nothing_the_registry_joins(corpus: str) -> None:
    """Keys, figures, warnings, unknown groups and declared classes are unchanged."""
    before, _none = _built(corpus, rename=False)
    after, renamed = _built(corpus, rename=True)
    assert renamed > 0, "the corpus carries no display name, so the arm grades nothing"
    same = nameless(before) == nameless(after)
    assert same
    keys_before = tuple(sorted(before.items)), tuple(sorted(before.recipes))
    keys_after = tuple(sorted(after.items)), tuple(sorted(after.recipes))
    assert keys_after == keys_before
    assert after.warnings == before.warnings
    assert after.unknown_groups == before.unknown_groups


@pytest.mark.parametrize("corpus", sorted(CORPORA))
def test_the_rename_really_reaches_the_built_registry(corpus: str) -> None:
    """The control: the built display names moved, and only by the prefix."""
    before, _none = _built(corpus, rename=False)
    after, _renamed = _built(corpus, rename=True)
    old = _display_names(before)
    new = _display_names(after)
    moved = sum(1 for was, now in zip(old, new, strict=True) if was != now)
    prefixed = sum(1 for was, now in zip(old, new, strict=True) if now == RENAME_PREFIX + was)
    assert moved > 0
    assert prefixed == moved
