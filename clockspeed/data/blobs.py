"""Parsers for the two Unreal text-serialization grammars in the game docs file.

Unreal serializes struct arrays into the docs JSON as opaque TEXT. Every scalar
in that document is a string - a duration arrives as ``'2.000000'``, not as a
float - so a secondary parse is universal rather than exceptional. Two of those
text grammars carry the recipe graph, and this module owns both.

WHY THIS IS A MODULE OF ITS OWN, WITH NO IMPORTS BEYOND THE STANDARD LIBRARY:
it is pure string-to-value transformation and it must stay that way. Nothing
here opens a file, knows where the game is installed, or knows what a save is.
That is not minimalism for its own sake - it is what makes the grammar testable
on a machine with no game on it, which is the acceptance condition the data
layer is held to. A parser that needed the install to prove itself could only
ever be tested where the bug already lived.

WHY TWO PARSERS AND NOT ONE:
the grammars look alike and are not. Both are paren-wrapped, comma-separated
lists of quoted paths, so a single tolerant parser would happily return a
plausible tuple built from the wrong grammar and nothing downstream could tell.

    item-amount (mIngredients, mProduct)
        blob     := "" | "(" entry { "," entry } ")"
        entry    := "(ItemClass=" qpath ",Amount=" integer ")"
        qpath    := '"' typename "'" objectpath "." classname "'" '"'

    class-path (mProducedIn)
        blob     := "" | "(" qstring { "," qstring } ")"
        qstring  := '"' objectpath '"'

The class-path entries are BARE quoted paths: no ``Type'...'`` wrapper, no
``ItemClass=``, no ``Amount=``. Reusing either parser for the other grammar is
the mistake this split exists to make impossible.

THE ONE FACT THAT BREAKS A NAIVE IMPLEMENTATION:
the field delimiter is the DOUBLE quote, and a SINGLE quote sits inside the
value as part of Unreal's ``Type'Path'`` object-reference syntax. Splitting on
the single quote first corrupts every path, and corrupts it invisibly - the
result is still a string, still looks like a path, and still yields a trailing
token that resembles an item key. Split on the double quote first. That is why
the entry pattern below anchors on ``"([^"]*)"`` and never looks at ``'`` at
all. Relatedly, there is NO backslash escaping inside these blobs once the JSON
layer has decoded them, so there is deliberately no unescaper here; backslashes
seen in a Python ``repr`` of one of these values are ``repr`` quoting the
embedded single quote, not data.

WHY PARTIAL SUCCESS RAISES INSTEAD OF RETURNING WHAT IT MANAGED:
a blob that half-parses yields a SHORT ingredient list, and a short ingredient
list is a wrong production ratio that no test downstream can distinguish from a
right one. There is no safe way to report "most of the recipe". So every
non-empty blob is accounted for character by character - entries must tile the
inside of the wrapper end to end, separated by single commas - and anything
left over is a :class:`BlobParseError`. The intent is that a future game patch
which changes this grammar produces a red build rather than a silently thinner
factory plan. Callers that want to flag-and-skip unknown content own that
policy and catch this error; this layer will not make the choice for them.

WHAT THIS MODULE DELIBERATELY DOES NOT DO:
it does not convert units. Amounts are returned verbatim. Solids are plain item
counts while liquids and gases are in litres, and which of those applies is a
property of the ITEM - it lives on the descriptor, in a different group of the
same file - so it is simply not knowable from a blob. Two measured amounts are
not even whole cubic metres (2500 and 1500), so a caller that divides by 1000
into an int loses half a cubic metre per cycle in silence. Normalization
belongs after the descriptor join, in exact rational arithmetic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = [
    "BlobParseError",
    "ItemAmount",
    "marker_count",
    "parse_class_paths",
    "parse_item_amounts",
]

# The literal counted by marker_count. Deliberately a plain string and not a
# pattern: its value is that it shares no logic with the parser (see the
# marker_count docstring).
_ITEM_AMOUNT_MARKER = "(ItemClass="

# The pattern measured against every item-amount chunk in the shipped docs
# file, matching all of them with zero failures. Two properties are load
# bearing. First, the value is delimited by the double quote and ``[^"]*``
# steps straight over the embedded single quote. Second, the amount character
# class admits a minus sign: no negative amount has ever been observed, but a
# pattern that admits one and then drops it silently would be the worst of both
# choices, so a sign is parsed and preserved.
_ENTRY_RE = re.compile(r'\(ItemClass="([^"]*)",Amount=([-0-9]+)\)')

# The class-path grammar: a bare quoted path, no keys and no type wrapper.
_QUOTED_PATH_RE = re.compile(r'"([^"]*)"')

# Error messages quote the offending blob so a grammar change is diagnosable
# from the failure alone, but a docs field can be long and an unbounded echo
# turns one bad row into an unreadable wall.
_EXCERPT_LIMIT = 160


@dataclass(frozen=True)
class ItemAmount:
    """One item reference and its amount, lifted verbatim out of a blob.

    Frozen because a parsed entry is a reading of the shipped data, not a
    working value. Nothing downstream has any business editing one, and
    immutability makes it usable as a dictionary key during the descriptor
    join that follows.

    Attributes:
        item_key: The trailing token after the final ``.`` with the closing
            single quote stripped, for example ``Desc_OreIron_C``. Falls back
            to the whole of ``raw_path`` when the path carries no ``.`` at
            all - the validated pattern admits such a path, and inventing a
            key or dropping the entry would both be worse than saying plainly
            what was there.
        raw_path: The full path exactly as it appeared between the double
            quotes, unmodified, embedded single quote included. Kept whole
            because it is the only evidence available if ``item_key`` ever
            fails to resolve.
        amount: The integer exactly as written in the blob. NOT unit
            converted - see the module docstring; units are not knowable from
            a blob.
    """

    item_key: str
    raw_path: str
    amount: int


class BlobParseError(ValueError):
    """Raised when a non-empty blob cannot be fully accounted for.

    A :class:`ValueError` subclass so a caller already guarding a conversion
    can catch it broadly, while a caller that specifically wants to flag
    unknown game content and continue can catch it precisely.
    """


def _excerpt(blob: str) -> str:
    """Return a length-bounded copy of ``blob`` for an error message.

    Args:
        blob: The offending blob.

    Returns:
        The blob, truncated with a trailing ellipsis if it is long.
    """
    if len(blob) <= _EXCERPT_LIMIT:
        return blob
    return blob[:_EXCERPT_LIMIT] + "..."


def _trailing_token(raw_path: str) -> str:
    """Return the class name at the end of an Unreal object path.

    The key is the token after the FINAL ``.``, with the closing single quote
    of the ``Type'Path'`` wrapper stripped. A path with no ``.`` is returned
    whole rather than treated as an error: the class-path grammar is full of
    ``/Script/<Module>.<Class>`` engine references that resolve to nothing
    buildable, and being unresolvable is a fact for the caller to act on, not
    a parse failure.

    Args:
        raw_path: A path exactly as it appeared inside the double quotes.

    Returns:
        The trailing token, or the whole path when there is no ``.``.
    """
    return raw_path.rsplit(".", 1)[-1].removesuffix("'")


def _scan(blob: str, pattern: re.Pattern[str], grammar: str) -> tuple[re.Match[str], ...]:
    """Tile ``pattern`` across a paren-wrapped comma-separated blob, or raise.

    Full accounting is the point. The wrapper must be present, the entries
    must cover the inside of it end to end, and consecutive entries must be
    separated by exactly one comma. Any character not consumed by that walk is
    material the measured grammar does not explain, and this refuses rather
    than returning the entries it happened to recognise first.

    Nesting is exactly two levels deep in the measured data and never deeper,
    so this walk is flat by design; a recursive descent would accept shapes
    that would be a grammar change worth failing on.

    Args:
        blob: A non-empty blob, wrapper included.
        pattern: The entry pattern for one of the two grammars.
        grammar: Grammar name, used only in error messages.

    Returns:
        One match per entry, in source order.

    Raises:
        BlobParseError: If the wrapper is missing, an entry does not match, or
            any character is left unaccounted for.
    """
    if not blob.startswith("(") or not blob.endswith(")"):
        raise BlobParseError(f"{grammar} blob is not paren-wrapped: {_excerpt(blob)!r}")

    inner = blob[1:-1]
    matches: list[re.Match[str]] = []
    position = 0
    # Offsets in the messages below are reported against the ORIGINAL blob, so
    # the +1 for the wrapper character this walk has already stepped past.
    while True:
        match = pattern.match(inner, position)
        if match is None:
            raise BlobParseError(
                f"{grammar} blob does not match the measured grammar at offset "
                f"{position + 1}: {_excerpt(blob)!r}"
            )
        matches.append(match)
        position = match.end()
        if position >= len(inner):
            return tuple(matches)
        if inner[position] != ",":
            raise BlobParseError(
                f"{grammar} blob has unaccounted material at offset "
                f"{position + 1}: {_excerpt(blob)!r}"
            )
        position += 1


def parse_item_amounts(blob: str) -> tuple[ItemAmount, ...]:
    """Parse an item-amount blob into its entries.

    This is the grammar of ``mIngredients`` and ``mProduct``. Amounts come back
    verbatim; see the module docstring on why units cannot be resolved here.

    The empty string is a real and valid value, not an error - several recipes
    genuinely have no ingredients - and it yields an empty tuple. Every other
    input must be fully accounted for.

    Args:
        blob: The raw field value, possibly empty.

    Returns:
        One :class:`ItemAmount` per entry, in source order. Empty for an empty
        blob.

    Raises:
        BlobParseError: If a non-empty blob does not match the measured
            grammar end to end, or an amount is not an integer. Returning the
            entries parsed so far would be a silent short list, which is the
            failure this module exists to prevent.
    """
    if not blob:
        return ()

    entries: list[ItemAmount] = []
    for match in _scan(blob, _ENTRY_RE, "item-amount"):
        raw_path, digits = match.group(1), match.group(2)
        try:
            amount = int(digits)
        except ValueError as error:
            # Reachable: the validated character class admits strings such as
            # "1-2" that int() rejects. Refusing beats coercing.
            raise BlobParseError(
                f"item-amount blob has a non-integer Amount {digits!r}: {_excerpt(blob)!r}"
            ) from error
        entries.append(
            ItemAmount(
                item_key=_trailing_token(raw_path),
                raw_path=raw_path,
                amount=amount,
            )
        )
    return tuple(entries)


def parse_class_paths(blob: str) -> tuple[str, ...]:
    """Parse a class-path blob into its paths.

    This is the grammar of ``mProducedIn``: bare quoted paths with no type
    wrapper and no keys. Paths are returned WHOLE and unmodified, including the
    ones that resolve to nothing buildable - ``/Script/<Module>.<Class>``
    engine references have no corresponding asset entry, and some tokens carry
    no ``.`` separator at all. Dropping them here would erase the evidence that
    they were ever present; deciding what does not resolve is the caller's job.

    The empty string is a real and valid value and yields an empty tuple.

    Args:
        blob: The raw field value, possibly empty.

    Returns:
        Each quoted path verbatim, in source order. Empty for an empty blob.

    Raises:
        BlobParseError: If a non-empty blob does not match the measured
            grammar end to end.
    """
    if not blob:
        return ()
    return tuple(match.group(1) for match in _scan(blob, _QUOTED_PATH_RE, "class-path"))


def marker_count(blob: str) -> int:
    """Count literal ``(ItemClass=`` occurrences in ``blob``.

    THE CONTRACT, and the only reason this function exists: at extraction time
    the caller asserts ``marker_count(blob) == len(parse_item_amounts(blob))``
    and fails loudly when they disagree. That single assertion is what turns a
    future game patch's grammar change into a red build instead of a silently
    short ingredient list.

    Its value comes entirely from being NAIVE. It shares no code, no pattern
    and no assumption with the parser, so the two cannot be wrong in the same
    way - which is exactly what a second implementation of the same grammar
    would be. The price of that independence is a known false positive: a
    marker embedded inside a path would inflate the count. No such path exists
    in the measured corpus, and the tradeoff is deliberate. Do not "fix" this
    by parsing here; that would delete the only independent signal.

    Args:
        blob: The raw field value, possibly empty.

    Returns:
        The number of literal marker occurrences. Zero for an empty blob.
    """
    return blob.count(_ITEM_AMOUNT_MARKER)
