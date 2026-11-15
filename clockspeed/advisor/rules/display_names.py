"""The one display-name rule every card family shares (CS-1379, CS-1384).

A card's tier 1 and tier 2 say a class, a fuel or a target by the registry's display name,
quoted, and otherwise by its key. Whether a name may be quoted, and how it reads quoted, is
one rule, so the plan family (``plan.py``) and the fuel family (``fuel.py``) cannot drift
apart: a name that one reads quoted the other reads quoted, byte for byte, and a name that
one refuses the other refuses.

A name is usable when it is printable ASCII with a visible character, which is the engine's
own test of a card's text, is whitespace-normal - no leading or trailing space and no run of
two, which a card's tiers would collapse into a name the registry does not hold - and is at
most :data:`MAX_NAME_LENGTH` characters, measured on the name and never on its escaped text.
A separator or a quote in it is no bar: :func:`quoted` quotes and escapes it.
"""

from __future__ import annotations

from typing import Final, TypeGuard

#: The longest display name a tier reads. Far past any the pinned docs carry.
MAX_NAME_LENGTH: Final = 64


def usable_name(name: str | None) -> TypeGuard[str]:
    """Whether a tier may quote a display name in.

    Args:
        name: The display name, or None when the registry offers none.

    Returns:
        True when it is printable ASCII with a visible character, is whitespace-normal - no
        leading or trailing space and no run of two, which a card's tiers would collapse into
        a name the registry does not hold - and is at most :data:`MAX_NAME_LENGTH`
        characters, measured on the name and never on its escaped text. A separator or a
        quote in it is no bar: the label quotes and escapes it.
    """
    return (
        name is not None
        and len(name) <= MAX_NAME_LENGTH
        and name.strip(" ") != ""
        and all(" " <= ch <= "~" for ch in name)
        and " ".join(name.split()) == name
    )


def quoted(name: str) -> str:
    """Quote a usable display name, a backslash or double quote in it escaped by a backslash.

    The backslash is escaped first, so the backslash that escapes a quote is never doubled.

    Args:
        name: A name :func:`usable_name` passed.

    Returns:
        The name inside double quotes.
    """
    return '"' + name.replace("\\", "\\\\").replace('"', '\\"') + '"'
