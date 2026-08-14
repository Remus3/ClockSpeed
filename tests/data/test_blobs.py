"""Tests for the two Unreal text-serialization blob grammars in the docs file.

The parsers under test are the narrowest seam in the data layer and the
easiest place in this project to be silently, plausibly wrong. Both grammars
are paren-wrapped, comma-separated lists of quoted paths; they look almost
identical and are not; and a parser that confuses one for the other still
returns a tuple of strings. The failure this file exists to catch is therefore
not a crash. It is a SHORT LIST - an ingredient dropped without a word, which
surfaces much later as a production ratio that is quietly off.

Three decisions shape every test below, and each is a rule rather than taste.

- **Fixtures are hand-authored synthetic literals** (BOOTSTRAP.md section 8.1).
  Never a slice of real game data, and never a real display name - display
  names carry non-ASCII and would trip the character-set gate. They are also
  not produced by a helper that mirrors the parser's own idea of the grammar:
  CONVENTIONS.md section 7.2 records that fixtures built parallel to the
  implementation stay green straight through the real defect. The wrapper
  punctuation is pinned once by a fixture written out character for character
  (``_ANCHOR_BLOB``), and the rest compose that verified shape with synthetic
  paths so the intent of each case stays readable.
- **Assertions pin the WHOLE result, never one field.** CONVENTIONS.md
  section 7.2 again: a partial or negative assertion passes for the correct
  output and for a collapsed one alike. Comparing the full tuple of frozen
  ``ItemAmount`` values is the only assertion shape that cannot pass a short
  list, which is the entire failure mode this module guards.
- **The awkward measured cases are here on purpose.** The embedded single
  quote inside the double-quoted value, a fluid amount that is not a multiple
  of 1000, a ``/Script/`` token with no ``.`` separator, the empty string as a
  real and valid value, and a negative amount the validated regex admits but
  the corpus never showed. Each of those breaks a different naive
  implementation, and each is measured, not imagined - the source is the S3
  section of the spike report in ``docs/_archive/``.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from clockspeed.data.blobs import (
    BlobParseError,
    ItemAmount,
    marker_count,
    parse_class_paths,
    parse_item_amounts,
)

# ---------------------------------------------------------------------------
# Synthetic item paths - exactly as they appear INSIDE a blob's double quotes
# ---------------------------------------------------------------------------

_WIDGET_PATH = "/Script/Engine.BlueprintGeneratedClass'/Game/Synth/Desc_Widget.Desc_Widget_C'"
_GADGET_PATH = "/Script/Engine.BlueprintGeneratedClass'/Game/Synth/Desc_Gadget.Desc_Gadget_C'"
_SLUDGE_PATH = "/Script/Engine.BlueprintGeneratedClass'/Game/Synth/Desc_Sludge.Desc_Sludge_C'"
_ACID_PATH = "/Script/Engine.BlueprintGeneratedClass'/Game/Synth/Desc_Acid.Desc_Acid_C'"
_BRINE_PATH = "/Script/Engine.BlueprintGeneratedClass'/Game/Synth/Desc_Brine.Desc_Brine_C'"

# ---------------------------------------------------------------------------
# Item-amount blobs (the mIngredients and mProduct grammar)
# ---------------------------------------------------------------------------

# The one fixture spelled out character for character rather than composed.
# It is the anchor for every other blob here: it pins the delimiter ORDER -
# the double quote is the field delimiter and the single quote sits INSIDE
# the value as part of Unreal's Type'Path' syntax. A parser that splits on the
# single quote first corrupts every path, and the corruption is invisible
# unless the raw path is asserted whole.
_ANCHOR_BLOB = (
    '((ItemClass="/Script/Engine.BlueprintGeneratedClass'
    "'/Game/Synth/Desc_Anchor.Desc_Anchor_C'\",Amount=7))"
)
_ANCHOR_PATH = "/Script/Engine.BlueprintGeneratedClass'/Game/Synth/Desc_Anchor.Desc_Anchor_C'"

_ONE_ENTRY_BLOB = f'((ItemClass="{_WIDGET_PATH}",Amount=1))'

_TWO_ENTRY_BLOB = f'((ItemClass="{_WIDGET_PATH}",Amount=1),(ItemClass="{_GADGET_PATH}",Amount=4))'
_TWO_ENTRY_EXPECTED = (
    ItemAmount(item_key="Desc_Widget_C", raw_path=_WIDGET_PATH, amount=1),
    ItemAmount(item_key="Desc_Gadget_C", raw_path=_GADGET_PATH, amount=4),
)

# A recipe with a byproduct: two products, the second a fluid in litres.
_BYPRODUCT_BLOB = (
    f'((ItemClass="{_GADGET_PATH}",Amount=2),(ItemClass="{_SLUDGE_PATH}",Amount=1000))'
)

# The measured Recipe_Battery_C shape: fluid amounts that are NOT multiples of
# 1000. Any code that divides by 1000 into an int loses half a cubic metre per
# cycle in silence.
_FRACTIONAL_FLUID_BLOB = (
    f'((ItemClass="{_ACID_PATH}",Amount=2500),(ItemClass="{_BRINE_PATH}",Amount=1500))'
)

# The regex validated against all 2440 measured chunks admits a minus sign
# even though no negative amount was observed. Admitting it and dropping it
# would be the worst of both.
_NEGATIVE_AMOUNT_BLOB = f'((ItemClass="{_WIDGET_PATH}",Amount=-3))'

# A path carrying no "." at all, so the trailing-token rule has nothing to cut.
_DOTLESS_ITEM_PATH = "/Script/SynthGame"
_DOTLESS_ITEM_BLOB = f'((ItemClass="{_DOTLESS_ITEM_PATH}",Amount=1))'

# A path that happens to contain the literal marker text. Nothing in the
# measured corpus looks like this; it exists to pin what marker_count IS - a
# naive literal count deliberately kept independent of the parser.
_EMBEDDED_MARKER_PATH = (
    "/Script/Engine.BlueprintGeneratedClass'/Game/Synth/(ItemClass=/Desc_Odd.Desc_Odd_C'"
)
_EMBEDDED_MARKER_BLOB = f'((ItemClass="{_EMBEDDED_MARKER_PATH}",Amount=1))'

# --- malformed, one failure mode each --------------------------------------

# Nesting is exactly two levels: 0 of 2616 non-empty values were not
# paren-wrapped, so a single-level blob is a grammar change, not a variant.
_UNWRAPPED_BLOB = f'(ItemClass="{_WIDGET_PATH}",Amount=1)'

# One good entry followed by material the grammar cannot account for. This is
# the exact case where returning the one parsed entry would be a silent short
# list, so it must raise instead.
_TRAILING_JUNK_BLOB = f'((ItemClass="{_WIDGET_PATH}",Amount=1)garbage)'

# Two markers, the first entry missing its Amount key: marker_count sees two,
# a parser must refuse rather than report one.
_MISSING_AMOUNT_BLOB = f'((ItemClass="{_WIDGET_PATH}"),(ItemClass="{_GADGET_PATH}",Amount=2))'

# The character class admits "1-2", which is not an integer.
_NON_INTEGER_AMOUNT_BLOB = f'((ItemClass="{_WIDGET_PATH}",Amount=1-2))'

# ---------------------------------------------------------------------------
# Class-path blobs (the mProducedIn grammar - bare quoted paths, no keys)
# ---------------------------------------------------------------------------

_BUILD_PATH = "/Game/Synth/Build_Synthesizer.Build_Synthesizer_C"
_BENCH_PATH = "/Game/Synth/BP_SynthBench.BP_SynthBench_C"

# The measured awkward case: a /Script/<Module>.<Class> engine reference with
# no corresponding Build_* asset, and a token with no "." separator at all.
# Neither resolves to a building. Resolution is the caller's problem; dropping
# them here would hide the fact that they were ever present.
_ENGINE_CLASS_PATH = "/Script/SynthGame.FGSynthAutomatedWorkBench"
_DOTLESS_CLASS_PATH = "/Script/SynthGame"

_PRODUCED_IN_THREE_BLOB = f'("{_BUILD_PATH}","{_BENCH_PATH}","{_ENGINE_CLASS_PATH}")'
_PRODUCED_IN_ONE_BLOB = f'("{_BUILD_PATH}")'
_PRODUCED_IN_UNRESOLVABLE_BLOB = f'("{_ENGINE_CLASS_PATH}","{_DOTLESS_CLASS_PATH}")'

# A space where the comma belongs.
_MALFORMED_PRODUCED_IN_BLOB = f'("{_BUILD_PATH}" "{_BENCH_PATH}")'


# ---------------------------------------------------------------------------
# The empty string is a real and valid value, not an error
# ---------------------------------------------------------------------------


def test_empty_item_amount_blob_is_a_valid_empty_result_not_an_error():
    assert parse_item_amounts("") == ()


def test_empty_class_path_blob_is_a_valid_empty_result_not_an_error():
    assert parse_class_paths("") == ()


# ---------------------------------------------------------------------------
# The item-amount grammar
# ---------------------------------------------------------------------------


def test_raw_path_survives_the_embedded_single_quote_intact():
    # The whole point: the value between the double quotes contains a single
    # quote, and it comes back byte for byte. Asserting the tuple whole means
    # a truncated path cannot slip through as a merely-different item_key.
    assert parse_item_amounts(_ANCHOR_BLOB) == (
        ItemAmount(item_key="Desc_Anchor_C", raw_path=_ANCHOR_PATH, amount=7),
    )


def test_single_entry_blob_yields_exactly_one_item_amount():
    assert parse_item_amounts(_ONE_ENTRY_BLOB) == (
        ItemAmount(item_key="Desc_Widget_C", raw_path=_WIDGET_PATH, amount=1),
    )


def test_multi_entry_blob_yields_every_entry_in_source_order():
    assert parse_item_amounts(_TWO_ENTRY_BLOB) == _TWO_ENTRY_EXPECTED


def test_byproduct_blob_yields_both_products():
    assert parse_item_amounts(_BYPRODUCT_BLOB) == (
        ItemAmount(item_key="Desc_Gadget_C", raw_path=_GADGET_PATH, amount=2),
        ItemAmount(item_key="Desc_Sludge_C", raw_path=_SLUDGE_PATH, amount=1000),
    )


def test_fluid_amounts_are_verbatim_and_never_unit_converted_here():
    # 2500 and 1500 are the measured Recipe_Battery_C amounts, in litres. The
    # scale factor is a property of the ITEM - mForm lives on the descriptor,
    # in a different group - so this layer cannot know the units and must not
    # guess at them. Any conversion happens after the descriptor join, in
    # exact rational arithmetic.
    assert parse_item_amounts(_FRACTIONAL_FLUID_BLOB) == (
        ItemAmount(item_key="Desc_Acid_C", raw_path=_ACID_PATH, amount=2500),
        ItemAmount(item_key="Desc_Brine_C", raw_path=_BRINE_PATH, amount=1500),
    )


def test_negative_amount_is_preserved_rather_than_silently_dropped():
    assert parse_item_amounts(_NEGATIVE_AMOUNT_BLOB) == (
        ItemAmount(item_key="Desc_Widget_C", raw_path=_WIDGET_PATH, amount=-3),
    )


def test_item_key_falls_back_to_the_whole_path_when_there_is_no_dot():
    assert parse_item_amounts(_DOTLESS_ITEM_BLOB) == (
        ItemAmount(
            item_key=_DOTLESS_ITEM_PATH,
            raw_path=_DOTLESS_ITEM_PATH,
            amount=1,
        ),
    )


# ---------------------------------------------------------------------------
# Partial success is failure
# ---------------------------------------------------------------------------


def test_unwrapped_single_level_blob_raises():
    with pytest.raises(BlobParseError):
        parse_item_amounts(_UNWRAPPED_BLOB)


def test_trailing_junk_raises_rather_than_returning_a_short_list():
    with pytest.raises(BlobParseError):
        parse_item_amounts(_TRAILING_JUNK_BLOB)


def test_entry_missing_its_amount_key_raises():
    with pytest.raises(BlobParseError):
        parse_item_amounts(_MISSING_AMOUNT_BLOB)


def test_amount_that_is_not_an_integer_raises_rather_than_being_dropped():
    with pytest.raises(BlobParseError):
        parse_item_amounts(_NON_INTEGER_AMOUNT_BLOB)


def test_blob_parse_error_is_a_value_error_so_callers_can_catch_broadly():
    assert issubclass(BlobParseError, ValueError)


# ---------------------------------------------------------------------------
# The class-path grammar - a DIFFERENT grammar, not a reused parser
# ---------------------------------------------------------------------------


def test_class_path_blob_with_three_entries_returns_all_three_in_order():
    assert parse_class_paths(_PRODUCED_IN_THREE_BLOB) == (
        _BUILD_PATH,
        _BENCH_PATH,
        _ENGINE_CLASS_PATH,
    )


def test_class_path_blob_with_one_entry_returns_that_entry():
    assert parse_class_paths(_PRODUCED_IN_ONE_BLOB) == (_BUILD_PATH,)


def test_unresolvable_script_tokens_are_returned_intact_not_dropped():
    assert parse_class_paths(_PRODUCED_IN_UNRESOLVABLE_BLOB) == (
        _ENGINE_CLASS_PATH,
        _DOTLESS_CLASS_PATH,
    )


def test_malformed_class_path_blob_raises():
    with pytest.raises(BlobParseError):
        parse_class_paths(_MALFORMED_PRODUCED_IN_BLOB)


def test_the_two_grammars_reject_each_other():
    # Agreement between two similar-looking parsers is not evidence that
    # either is right. Each must refuse the other's input outright, because a
    # tolerant parser here returns a plausible tuple built from the wrong
    # grammar and nothing downstream can tell.
    with pytest.raises(BlobParseError):
        parse_item_amounts(_PRODUCED_IN_THREE_BLOB)
    with pytest.raises(BlobParseError):
        parse_class_paths(_ONE_ENTRY_BLOB)


# ---------------------------------------------------------------------------
# marker_count - the caller's canary against a future grammar change
# ---------------------------------------------------------------------------


def test_marker_count_of_an_empty_blob_is_zero():
    assert marker_count("") == 0


def test_marker_count_matches_the_parsed_length_for_a_well_formed_blob():
    # This is the assertion the extractor makes at extraction time. Stating it
    # here means the contract is tested, not merely documented.
    #
    # The parsed tuple is pinned FIRST and in full, and that ordering is
    # load-bearing rather than tidy: an implementation that parsed nothing and
    # counted nothing satisfies "count equals length" perfectly. Measured
    # against the inert stub during this module's own TDD run, the count-only
    # form of this test passed 0 == 0. A comparison between two quantities is
    # only evidence once at least one of them is pinned to a known value.
    parsed = parse_item_amounts(_TWO_ENTRY_BLOB)
    assert parsed == _TWO_ENTRY_EXPECTED
    assert marker_count(_TWO_ENTRY_BLOB) == len(parsed)


def test_marker_count_sees_a_marker_the_parser_refuses_to_account_for():
    # Two markers present, one entry malformed. The count is what a well-formed
    # two-entry blob would parse to, yet parsing refuses outright - which is
    # exactly the red build the canary exists to produce.
    assert marker_count(_MISSING_AMOUNT_BLOB) == len(_TWO_ENTRY_EXPECTED)
    with pytest.raises(BlobParseError):
        parse_item_amounts(_MISSING_AMOUNT_BLOB)


def test_marker_count_is_a_naive_literal_count_not_a_second_parser():
    # Its independence from the parser is the whole value: two agreeing
    # implementations of the same grammar would fail the same way. The price
    # of that independence is this case, where a marker embedded in a path
    # inflates the count. It is documented rather than fixed.
    parsed = parse_item_amounts(_EMBEDDED_MARKER_BLOB)
    assert parsed == (
        ItemAmount(
            item_key="Desc_Odd_C",
            raw_path=_EMBEDDED_MARKER_PATH,
            amount=1,
        ),
    )
    assert marker_count(_EMBEDDED_MARKER_BLOB) > len(parsed)


# ---------------------------------------------------------------------------
# The published seam
# ---------------------------------------------------------------------------


def test_item_amount_rejects_mutation_so_a_parsed_entry_cannot_drift():
    entry = parse_item_amounts(_ONE_ENTRY_BLOB)[0]
    # setattr through a NAME rather than a string literal: ruff B010 rewrites
    # the literal form into a plain attribute assignment, which the type
    # checker then rejects on a frozen dataclass. The indirection keeps both
    # tools quiet without weakening what is asserted.
    attribute = "amount"
    with pytest.raises(FrozenInstanceError):
        setattr(entry, attribute, 0)


def test_item_amount_is_hashable_so_parsed_entries_can_key_a_lookup():
    entry = parse_item_amounts(_ONE_ENTRY_BLOB)[0]
    assert {entry: "ok"}[entry] == "ok"
