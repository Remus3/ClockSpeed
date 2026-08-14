"""Tests for clockspeed.data.docs_extract - encoding sniff, decode, group load.

Every input here is hand-authored synthetic bytes or a synthetic JSON string.
Nothing reads the real docs file, so this module runs green on a machine that
has never had the game installed - the phase 2 acceptance criterion
(BOOTSTRAP.md section 10, and the rule stated in tests/data/__init__.py).

The test that carries the most weight is
``test_sniff_encoding_classifies_by_bom_bytes_not_by_trial_decode``. The
measured trap (docs/_archive/spike-report-s1-s2-s3-s7.md section S1, restated
in BOOTSTRAP.md section 3.2) is that Python's utf-16 codec decodes UTF-8 bytes
WITHOUT raising and returns mojibake, while utf-8 decoding of UTF-16 bytes
fails loudly. The failure is asymmetric, so a try-decode-and-fall-back sniffer
ordered utf-16 first is silently wrong. That test asserts the sniffer gets it
right AND demonstrates, in the same test, that a trial decode would not have.

No display name, description or any other string lifted from the real game
data appears here. The en-US strings carry U+2014, smart quotes and 1305
occurrences of U+202F, and the character-set gate would correctly block them
(CONVENTIONS.md section 10). Non-ASCII test material is written as an escape
sequence, never as a literal character.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from clockspeed.data.docs_extract import (
    ENCODING_UTF8,
    ENCODING_UTF16,
    KEY_CLASSES,
    KEY_NATIVE_CLASS,
    KNOWN_GROUP_SHORT_NAMES,
    DocsDecodeError,
    DocsGroup,
    DocsStructureError,
    decode_docs_bytes,
    derive_short_name,
    index_by_short_name,
    load_document,
    load_groups,
    read_docs_text,
    sniff_encoding,
)
from clockspeed.data.version import pin

# ---------------------------------------------------------------------------
# Synthetic material
# ---------------------------------------------------------------------------

# The two NativeClass shapes measured in the real document: the fully wrapped
# Unreal object path (spike report S2, group 0) and the bare package-qualified
# token. Both must reduce to the same trailing class token.
WRAPPED_NATIVE_CLASS = "/Script/CoreUObject.Class'/Script/FactoryGame.FGResourceDescriptor'"
BARE_NATIVE_CLASS = "/Script/FactoryGame.FGRecipe"

# A group short name deliberately absent from the module's known-group table,
# standing in for game content this build has never seen (a patch, or a mod).
UNKNOWN_SHORT_NAME = "FGSyntheticUnknownThing"
UNKNOWN_NATIVE_CLASS = f"/Script/CoreUObject.Class'/Script/FactoryGame.{UNKNOWN_SHORT_NAME}'"

# U+FEFF written as an escape, never as a literal character. One of these was
# measured EMBEDDED inside an mDescription value, so a global strip of U+FEFF
# over the decoded text would corrupt a value (spike report S2).
EMBEDDED_BOM = "\ufeff"

# Every scalar in the real document is a string, including durations
# (spike report S2). The duration key really is misspelled in the game data.
DURATION_KEY = "mManufactoringDuration"
DURATION_VALUE = "2.000000"

EXPECTED_SHORT_NAMES = ("FGRecipe", "FGItemDescriptor", "FGBuildableManufacturer")
NO_GROUPS: tuple[DocsGroup, ...] = ()


def _group(native_class: str, entries: list[dict[str, str]]) -> dict[str, Any]:
    """Build one synthetic ``{NativeClass, Classes}`` group.

    Args:
        native_class: Verbatim NativeClass value.
        entries: Entry mappings for the group's Classes list.

    Returns:
        The group as a plain dict, ready for :func:`json.dumps`.
    """
    return {KEY_NATIVE_CLASS: native_class, KEY_CLASSES: entries}


def _three_group_document() -> list[dict[str, Any]]:
    """Build a three-group document covering both NativeClass shapes.

    Returns:
        A list of three well-formed groups whose short names are
        EXPECTED_SHORT_NAMES in order.
    """
    return [
        _group(
            BARE_NATIVE_CLASS,
            [{"ClassName": "Recipe_Synthetic_C", DURATION_KEY: DURATION_VALUE}],
        ),
        _group(
            "/Script/CoreUObject.Class'/Script/FactoryGame.FGItemDescriptor'",
            [{"ClassName": "Desc_Synthetic_C", "mForm": "RF_SOLID"}],
        ),
        _group(
            "/Script/CoreUObject.Class'/Script/FactoryGame.FGBuildableManufacturer'",
            [{"ClassName": "Build_Synthetic_C", "mPowerConsumption": "4.000000"}],
        ),
    ]


def _dumps(document: list[dict[str, Any]]) -> str:
    """Serialize a synthetic document to JSON text.

    Args:
        document: The group list.

    Returns:
        JSON text with non-ASCII characters left as real characters, so the
        decode path sees them rather than an escape sequence.
    """
    return json.dumps(document, ensure_ascii=False)


def _even_utf8(text: str) -> bytes:
    """Encode ``text`` as UTF-8, padded to an even byte count.

    An odd-length byte string makes the utf-16 codec raise "truncated data",
    which would mask the trap under test rather than demonstrate it. The real
    UTF-8 sibling in the locale directory is 5181010 bytes - even - so padding
    to even reproduces the measured situation rather than dodging it.

    Args:
        text: The document text.

    Returns:
        UTF-8 bytes whose length is even.
    """
    raw = text.encode("utf-8")
    if len(raw) % 2:
        raw += b" "
    return raw


# ---------------------------------------------------------------------------
# sniff_encoding - byte patterns only, never a trial decode
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("head", "expected"),
    [
        # The measured first four bytes of the real en-US.json.
        (b"\xff\xfe[\x00", ENCODING_UTF16),
        # The measured first four bytes of the real UTF-8 sibling.
        (b"[\r\n\t", ENCODING_UTF8),
        (b"[\r\n\t{", ENCODING_UTF8),
        # Big-endian BOM.
        (b"\xfe\xff\x00[", ENCODING_UTF16),
        # UTF-8 BOM.
        (b"\xef\xbb\xbf[", ENCODING_UTF8),
        # BOM-less UTF-16 LE: the null lands in the second byte.
        (b"[\x00{\x00", ENCODING_UTF16),
    ],
)
def test_sniff_encoding_classifies_from_leading_bytes(head: bytes, expected: str) -> None:
    assert sniff_encoding(head) == expected


def test_sniff_encoding_classifies_by_bom_bytes_not_by_trial_decode() -> None:
    """The whole point of this slice: a trial-decode sniffer is silently wrong.

    Measured in spike report S1: the utf-16 codec decodes the UTF-8 sibling
    without raising and returns mojibake, so "try utf-16, fall back to utf-8"
    reports success on the wrong encoding. This test asserts the correct
    classification and then demonstrates, on the same bytes, that the trial
    decode would have chosen utf-16.
    """
    raw = _even_utf8(_dumps(_three_group_document()))

    assert sniff_encoding(raw[:4]) == ENCODING_UTF8
    assert decode_docs_bytes(raw) == raw.decode("utf-8")

    # The demonstration. If this raised, a trial-decode sniffer would have been
    # sound and this slice would not need to exist.
    mojibake = raw.decode("utf-16")
    assert mojibake != raw.decode("utf-8")
    with pytest.raises(json.JSONDecodeError):
        json.loads(mojibake)


def test_sniff_encoding_is_asymmetric_utf8_fails_loudly_on_utf16_bytes() -> None:
    """The other half of the asymmetry, which is why utf-16-first ordering loses."""
    raw = _dumps(_three_group_document()).encode("utf-16")

    assert sniff_encoding(raw[:4]) == ENCODING_UTF16
    with pytest.raises(UnicodeDecodeError):
        raw.decode("utf-8")


# ---------------------------------------------------------------------------
# decode_docs_bytes
# ---------------------------------------------------------------------------


def test_decode_docs_bytes_consumes_the_leading_utf16_bom() -> None:
    text = _dumps(_three_group_document())
    raw = text.encode("utf-16")

    assert raw[:2] == b"\xff\xfe"
    decoded = decode_docs_bytes(raw)

    assert decoded == text
    assert not decoded.startswith(EMBEDDED_BOM)


def test_decode_docs_bytes_round_trips_utf8_without_a_bom() -> None:
    text = _dumps(_three_group_document())

    assert decode_docs_bytes(text.encode("utf-8")) == text


def test_decode_docs_bytes_keeps_a_bom_embedded_inside_a_value() -> None:
    """A U+FEFF inside a value is data. Only the leading BOM is a BOM."""
    described = f"a{EMBEDDED_BOM}b"
    document = [_group(BARE_NATIVE_CLASS, [{"ClassName": "X_C", "mDescription": described}])]
    raw = _dumps(document).encode("utf-16")

    decoded = decode_docs_bytes(raw)

    assert not decoded.startswith(EMBEDDED_BOM)
    assert EMBEDDED_BOM in decoded
    reparsed = json.loads(decoded)
    assert reparsed[0][KEY_CLASSES][0]["mDescription"] == described


def test_decode_docs_bytes_raises_on_bytes_that_are_not_the_sniffed_encoding() -> None:
    with pytest.raises(DocsDecodeError):
        decode_docs_bytes(b"\x5b\xff\xfe\xff")


# ---------------------------------------------------------------------------
# read_docs_text
# ---------------------------------------------------------------------------


def test_read_docs_text_decodes_a_utf16_file_from_disk(tmp_path: Path) -> None:
    text = _dumps(_three_group_document())
    path = tmp_path / "synthetic-docs.json"
    path.write_bytes(text.encode("utf-16"))

    assert read_docs_text(path) == text


def test_read_docs_text_does_not_modify_the_file_it_reads(tmp_path: Path) -> None:
    """Non-negotiable 1: never write to the game install. Assert it, do not assume it."""
    raw = _dumps(_three_group_document()).encode("utf-16")
    path = tmp_path / "synthetic-docs.json"
    path.write_bytes(raw)
    before = path.stat()

    read_docs_text(path)

    after = path.stat()
    assert path.read_bytes() == raw
    assert after.st_mtime_ns == before.st_mtime_ns
    assert after.st_size == before.st_size


# ---------------------------------------------------------------------------
# derive_short_name
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("native_class", "expected"),
    [
        (WRAPPED_NATIVE_CLASS, "FGResourceDescriptor"),
        (BARE_NATIVE_CLASS, "FGRecipe"),
        (
            "/Script/FactoryGame.FGBuildableManufacturerVariablePower",
            "FGBuildableManufacturerVariablePower",
        ),
        ("  /Script/FactoryGame.FGSchematic  ", "FGSchematic"),
        ("FGRecipe", "FGRecipe"),
        ("/Script/FactoryGame", "FactoryGame"),
    ],
)
def test_derive_short_name_takes_the_trailing_class_token(native_class: str, expected: str) -> None:
    assert derive_short_name(native_class) == expected


# ---------------------------------------------------------------------------
# load_groups
# ---------------------------------------------------------------------------


def test_load_groups_returns_one_group_per_recognized_group() -> None:
    groups = load_groups(_dumps(_three_group_document()))

    assert tuple(group.short_name for group in groups) == EXPECTED_SHORT_NAMES
    assert groups[0].native_class == BARE_NATIVE_CLASS
    assert tuple(entry["ClassName"] for entry in groups[1].entries) == ("Desc_Synthetic_C",)


def test_load_groups_keeps_every_entry_value_as_a_string() -> None:
    """Slice D owns conversion. This layer must not coerce a duration to a float."""
    groups = load_groups(_dumps(_three_group_document()))

    duration = groups[0].entries[0][DURATION_KEY]
    assert duration == DURATION_VALUE
    assert isinstance(duration, str)


def test_load_groups_flags_and_skips_an_unrecognized_group() -> None:
    """Non-negotiable 7: unknown content is flagged and skipped, never fatal."""
    document = [*_three_group_document(), _group(UNKNOWN_NATIVE_CLASS, [{"ClassName": "Y_C"}])]

    groups = load_groups(_dumps(document))

    assert tuple(group.short_name for group in groups) == EXPECTED_SHORT_NAMES


def test_load_groups_logs_the_unrecognized_group_rather_than_dropping_it_silently(
    caplog: pytest.LogCaptureFixture,
) -> None:
    document = [_group(UNKNOWN_NATIVE_CLASS, [{"ClassName": "Y_C"}])]

    with caplog.at_level(logging.WARNING, logger="clockspeed.data.docs_extract"):
        assert load_groups(_dumps(document)) == NO_GROUPS

    assert UNKNOWN_SHORT_NAME in caplog.text


@pytest.mark.parametrize(
    ("malformed", "marker"),
    [
        ({KEY_CLASSES: [{"ClassName": "Z_C"}]}, "NativeClass"),
        ({KEY_NATIVE_CLASS: "", KEY_CLASSES: []}, "NativeClass"),
        ({KEY_NATIVE_CLASS: BARE_NATIVE_CLASS, KEY_CLASSES: {"not": "a list"}}, "Classes"),
        ({KEY_NATIVE_CLASS: BARE_NATIVE_CLASS}, "Classes"),
        (["not", "a", "mapping"], "mapping"),
        (None, "mapping"),
    ],
)
def test_load_groups_flags_and_skips_a_malformed_group(
    malformed: Any, marker: str, caplog: pytest.LogCaptureFixture
) -> None:
    document = [*_three_group_document(), malformed]

    with caplog.at_level(logging.WARNING, logger="clockspeed.data.docs_extract"):
        groups = load_groups(_dumps(document))

    assert tuple(group.short_name for group in groups) == EXPECTED_SHORT_NAMES
    assert marker in caplog.text


def test_load_groups_rejects_a_document_whose_root_is_not_a_list() -> None:
    """A broken document is not unknown content. It fails loudly."""
    with pytest.raises(DocsStructureError):
        load_groups(json.dumps({KEY_NATIVE_CLASS: BARE_NATIVE_CLASS}))


def test_load_groups_rejects_text_that_is_not_json() -> None:
    with pytest.raises(DocsStructureError):
        load_groups("this is not json")


# ---------------------------------------------------------------------------
# load_document - the published flag channel
# ---------------------------------------------------------------------------


def test_load_document_publishes_the_unknown_group_verbatim() -> None:
    """Flagged and skipped, not lost: the drift guard and slice D can see it."""
    document = [*_three_group_document(), _group(UNKNOWN_NATIVE_CLASS, [{"ClassName": "Y_C"}])]

    loaded = load_document(_dumps(document))

    assert loaded.unknown_short_names == (UNKNOWN_SHORT_NAME,)
    assert loaded.unknown[0].native_class == UNKNOWN_NATIVE_CLASS
    assert loaded.unknown[0].entries[0]["ClassName"] == "Y_C"
    assert tuple(group.short_name for group in loaded.all_groups) == (
        *EXPECTED_SHORT_NAMES,
        UNKNOWN_SHORT_NAME,
    )


def test_load_document_publishes_the_malformed_group_with_its_reason() -> None:
    document = [*_three_group_document(), {KEY_CLASSES: []}]

    loaded = load_document(_dumps(document))

    assert len(loaded.malformed) == len(loaded.skipped_indexes)
    assert loaded.skipped_indexes == (len(EXPECTED_SHORT_NAMES),)
    assert "NativeClass" in loaded.malformed[0].reason


def test_load_document_accepts_a_caller_supplied_known_set() -> None:
    """The whitelist is data, not a hardcoded table of names."""
    document = [_group(UNKNOWN_NATIVE_CLASS, [{"ClassName": "Y_C"}])]

    loaded = load_document(_dumps(document), known_short_names=frozenset({UNKNOWN_SHORT_NAME}))

    assert tuple(group.short_name for group in loaded.groups) == (UNKNOWN_SHORT_NAME,)
    assert loaded.unknown == NO_GROUPS


# ---------------------------------------------------------------------------
# The known-group table against the pinned build's own census
# ---------------------------------------------------------------------------
#
# "Unknown" has to mean "this build has never seen this group", or the flag
# stops carrying information. A table listing only the groups the registry
# happens to consume reports every other stock group as unknown on every single
# run, and a list that is wrong 93 times out of 114 is a list nobody reads -
# which is exactly how the one genuinely new group gets missed.
#
# The pin is the right cross-check and the only one available without an
# install: it is a census of the shipped document taken by
# tools/drift_guard.py --re-extract, and its group_entry_counts names every
# group the pinned build ships. Comparing the hand-maintained table against it
# is a real anti-drift control rather than the table agreeing with itself.


def pinned_group_short_names() -> set[str]:
    """Return every group short name the pinned build ships.

    Returns:
        The short names, read from the tracked pin's census.
    """
    census = pin()["census"]
    counts = census["group_entry_counts"]
    assert isinstance(counts, dict)
    return set(counts)


def test_the_pin_census_actually_names_groups_so_the_comparison_is_not_vacuous() -> None:
    """The cross-check below is only evidence if the pin really carries names.

    An empty set compares equal to nothing and would make the next test pass
    against a table that had been emptied (CONVENTIONS.md section 15.1: an
    empty result is a claim about the pattern, not about the artifact).
    """
    names = pinned_group_short_names()
    assert len(names) == pin()["census"]["group_count"]
    assert "FGRecipe" in names


def test_every_group_the_pinned_build_ships_is_recognized_rather_than_unknown() -> None:
    """The known-group table covers the pinned build's whole group census.

    A stock group missing from the table is reported unknown on every build,
    and it is also skipped by the registry - which is how ten fluid item
    descriptors ended up published in litres under a contract that promises
    cubic metres.
    """
    missing = sorted(pinned_group_short_names() - KNOWN_GROUP_SHORT_NAMES)
    assert not missing, (
        f"{len(missing)} group(s) the pinned build ships are reported as unknown content: {missing}"
    )


def test_the_known_group_table_claims_no_group_the_pinned_build_does_not_ship() -> None:
    """Nothing is in the table that the pin cannot account for.

    The other direction matters just as much: a name kept in the table after
    the game stopped shipping it silences the unknown flag for a group that no
    longer exists, and the table slowly becomes fiction.
    """
    invented = sorted(KNOWN_GROUP_SHORT_NAMES - pinned_group_short_names())
    assert not invented, f"the known-group table names groups the pin does not: {invented}"


def test_a_group_the_pinned_build_never_shipped_is_still_reported_unknown() -> None:
    """Widening the table must not turn the unknown channel off.

    The positive half of the test above. A table that simply accepted
    everything would satisfy both assertions above and publish nothing.
    """
    document = [*_three_group_document(), _group(UNKNOWN_NATIVE_CLASS, [{"ClassName": "Y_C"}])]

    loaded = load_document(_dumps(document))

    assert UNKNOWN_SHORT_NAME not in pinned_group_short_names()
    assert loaded.unknown_short_names == (UNKNOWN_SHORT_NAME,)


# ---------------------------------------------------------------------------
# index_by_short_name
# ---------------------------------------------------------------------------


def test_index_by_short_name_maps_every_group() -> None:
    groups = load_groups(_dumps(_three_group_document()))

    index = index_by_short_name(groups)

    assert tuple(index) == EXPECTED_SHORT_NAMES
    assert index["FGRecipe"].entries[0][DURATION_KEY] == DURATION_VALUE


def test_index_by_short_name_keeps_the_first_of_a_duplicated_short_name(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A duplicate is a mod or a patch artifact: logged and skipped, never fatal."""
    first = DocsGroup(BARE_NATIVE_CLASS, "FGRecipe", ({"ClassName": "First_C"},))
    second = DocsGroup("/Script/OtherMod.FGRecipe", "FGRecipe", ({"ClassName": "Second_C"},))

    with caplog.at_level(logging.WARNING, logger="clockspeed.data.docs_extract"):
        index = index_by_short_name([first, second])

    assert index["FGRecipe"].entries[0]["ClassName"] == "First_C"
    assert "FGRecipe" in caplog.text
