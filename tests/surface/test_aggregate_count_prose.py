"""CS-929 and CS-933 - the SHAPE of a restated route-set count, swept by shape.

THE DEFECT THIS CLOSES. ``clockspeed/surface/server.py`` said
``/api/advice/<id>/derivation`` and ``/api/advice/<id>/state`` "are two of the
NINE endpoints ``BOOTSTRAP.md`` section 7.1 publishes". The one owner of that
number, ``clockspeed/surface/api/health.py::ENDPOINT_TEMPLATES``, held ELEVEN by
the time this was written: ``/api/registry`` landed under CS-912 and ``/api/map``
under CS-977 and CS-980, and neither touched the docstring the sentence sat in.
``tests/surface/audit_harness.py`` records CS-912 falsifying the THIRD such
sentence in this repository. This one is the fourth.

WHY THIS IS NOT THE CS-927 DETECTOR WIDENED, which was MEASURED rather than
judged. Running ``tests/surface/test_pending_route_count.py``'s detector over
``server.py`` yields SEVEN false positives - every one a "two templates" phrase
about template COLLISION rather than a count - and ZERO hits on the actual stale
sentence. The reason is structural: the stale noun is "endpoints", and that
module's ``COUNTED_NOUNS`` deliberately omits it so ``pending.py`` may keep
saying "the five unbacked endpoints" about a subset it owns itself. Widening that
vocabulary either floods or misses, so this module builds the right detector
instead of stretching the wrong one. That detector stays scoped to ``pending.py``
and is not modified here.

THE POPULATION IS DEFINED BY SHAPE AND NEVER BY VALUE, which is the whole of
CS-933. That item was filed against ``clockspeed/surface/web/app.js``, which said
"The ten routes ``BOOTSTRAP.md`` section 7.1 publishes" - CORRECT on the day it
was filed, and invisible to every sweep that session because all of them hunted
the stale value NINE. A sweep keyed to the wrong value finds only the sites that
have already broken, which is the set you already knew about. So the shape
graded here is: A COUNT, of a noun naming the published route set, standing next
to a reference to the AUTHORITY that publishes it, with no owner named and no
guard behind it. The value is never consulted. :func:`test_a_correct_value_
restatement_reddens_the_guard` is the arm that separates this from a value sweep,
and without it this module would be the thing CS-933 exists to prevent.

THE AUTHORITY LEG IS WHAT KEEPS A LEGAL SUBSET LEGAL, and it is load-bearing
rather than decorative. ``pending.py`` says "the five unbacked endpoints" about
its OWN set, and that is a fact it owns; ``audit_harness.py`` says "it read
'four' from nine templates" as a historical record. Neither stands next to
``BOOTSTRAP.md`` or a section reference, so neither fires. Both directions are
pinned by their own arms, because a guard that reddens on a module counting its
own subset is a wrong guard, not a strict one.

THE AUTHORITY MAY SIT ON EITHER SIDE, and that too was measured rather than
assumed. ``docs/adr/0012`` spells the same defect with the clauses reversed -
"``BOOTSTRAP.md`` section 7.1 names nine endpoints" - so a detector that only
looked AFTER the noun would read that shape as clean. The window therefore spans
both directions and an arm plants each order.

WHAT IS OUT OF POPULATION, stated as a decision rather than left to a glob.
``docs/adr/`` is excluded ON PURPOSE. An ADR records what was decided WHEN it was
decided; correcting ``docs/adr/0012`` would rewrite history rather than fix
drift, and CS-929's note refuses it in so many words. That exclusion is not a
typo dressed as a policy: :func:`test_the_excluded_adr_would_redden_this_guard`
proves the excluded file DOES carry the shape, so the boundary is a deliberate
exclusion of a real hit. ``BOOTSTRAP.md`` section 7.1 is likewise out - it is the
document that ENUMERATES the set, so it is the one place a size may be spelled.

THE POPULATION IS READ FROM THE FILESYSTEM, not from ``git ls-files``. A guard
that enumerates through git cannot see an untracked file, so a new module is
green locally and red at commit time. Every ``.py``, ``.js`` and ``.html`` file
under ``clockspeed/`` is swept whether git knows about it or not, and the JS and
HTML carriers are in scope because ``app.js`` is the file CS-933 was filed
against - it is clean today by accident, not by construction.

WHAT THE MUTATION PASS CAUGHT IN THIS MODULE ITSELF, recorded because the two
survivors were both defects OF THE GUARD rather than of its subject, and both
are the shape CS-927's docstring warned about in the abstract. Dropping "eleven"
from :data:`COUNT_WORDS` survived with 143 arms green: the vocabulary sweep is
PARAMETRIZED over the vocabulary, so deleting a member deletes that member's own
arm. Dropping "bootstrapmd" from :data:`AUTHORITY_TOKENS` survived with all 149
green: every real carrier in this repository names both tokens - "``BOOTSTRAP.md``
section 7.1" - so no plant ever isolated either one. The repair is both directions
at once: each vocabulary's MEMBERSHIP is pinned against a literal authored
separately, and each authority token additionally gets a plant carrying that
token and no other, asserted to isolate it.

Test-quality discipline (CONVENTIONS.md section 7.2). Every population size is
bound to a SCALAR before it is asserted, so the pytest assertion channel renders
an integer rather than the collection behind it (CS-850). The population has its
own floor arm: a glob that matched nothing would make the one arm this item
exists for pass by measuring nothing at all. Nothing rendered here is a path from
this machine - the paths are repository-relative and the phrases are literals
authored in this repository or lifted from a tracked source file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest

from clockspeed.surface.api import health

# ---------------------------------------------------------------------------
# The detector
# ---------------------------------------------------------------------------

REPO_ROOT: Final = Path(__file__).resolve().parents[2]

#: Spelled number words this guard reads as a count. Swept member by member
#: below, so deleting one cannot leave the suite green. Deliberately NOT shared
#: with ``tools/drift_guard.py``'s duration vocabulary, for the reason
#: ``test_pending_route_count.py`` already states: a coupling that makes this
#: guard's meaning move whenever a CI duration spelling is added.
COUNT_WORDS: Final = (
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
    "twenty",
)

#: The nouns that name the PUBLISHED ROUTE SET. All three spellings appear in
#: this package's prose for the same set - "endpoints" in ``server.py``,
#: "routes" in ``app.js``, "templates" in ``pending.py`` - so a guard that
#: admitted only one of them would grade one carrier and miss the other two.
#: That is exactly how CS-929 and CS-933 came to be two items instead of none.
AGGREGATE_NOUNS: Final = (
    "endpoint",
    "endpoints",
    "route",
    "routes",
    "template",
    "templates",
)

#: A reference to WHO PUBLISHES the set. Its presence is what makes a count an
#: AGGREGATE count rather than a module counting its own subset, and its absence
#: is why "the five unbacked endpoints" stays legal.
AUTHORITY_TOKENS: Final = ("bootstrapmd", "section")

#: One plant per authority token, each carrying THAT TOKEN AND NO OTHER. Every
#: real carrier in this repository names both - "``BOOTSTRAP.md`` section 7.1" -
#: so a suite that only ever plants the pair leaves each member individually
#: unmeasured: a mutation deleting "bootstrapmd" survived the first pass of this
#: module with all arms green, because "section" alone still carried every plant.
AUTHORITY_PLANTS: Final = {
    "bootstrapmd": "the nine endpoints ``BOOTSTRAP.md`` publishes",
    "section": "the nine endpoints section 7.1 publishes",
}

#: How many tokens may sit between the count and the noun. Two, admitting
#: "nine endpoints" and "nine route templates" while leaving "two of the
#: endpoints" - a count of the PAIR under discussion, not of the set - below the
#: threshold. Pinned in both directions by its own arms.
NOUN_LOOKAHEAD: Final = 2

#: How far either side of the count-noun pair an authority reference is still
#: read as attached to it.
AUTHORITY_SPAN: Final = 6

#: A noun followed by this is distributive - a RATE, not a count. "One route per
#: published template" states a one-to-one correspondence and must never fire;
#: ``routes.py`` says it three times and ``pending.py`` once.
DISTRIBUTIVE_WORD: Final = "per"

#: Longest run of digits still read as a count of a route set. Three, so "11"
#: and "100" count and a build number does not.
MAX_DIGIT_RUN: Final = 3

#: Punctuation and markup stripped from a token's ends before asking whether it
#: is a bare integer. A section reference keeps its interior dot and therefore
#: never reduces to digits, which is what stops "section 7.1" reading as a count.
_EDGE_PUNCTUATION: Final = "(),.;:[]{}`\"'*#-"

#: Which file suffixes under ``clockspeed/`` carry prose this guard grades.
POPULATION_SUFFIXES: Final = (".py", ".js", ".html")

#: Where the population is rooted. The shipping package only: ``tests/`` records
#: the HISTORY of these sentences on purpose, and ``docs/adr/`` is excluded for
#: the reason the module docstring states.
POPULATION_ROOT_RELATIVE: Final = "clockspeed"

#: The ADR that spells this defect and is deliberately left alone.
EXCLUDED_ADR_RELATIVE: Final = "docs/adr/0012-dashboard-refusal-vocabulary-and-wire-form.md"


def _normalize(token: str) -> str:
    """Reduce one whitespace-separated token to its lowercase letters.

    Args:
        token: A single token in its original spelling.

    Returns:
        The token's letters, lowercased. A token with no letters reduces to the
        empty string and can therefore never match either vocabulary.
    """
    return "".join(character for character in token if character.isalpha()).lower()


def _is_count(token: str, normalized: str) -> bool:
    """Whether TOKEN spells a count, as a word or as bare digits.

    Args:
        token: The token in its original spelling, punctuation included.
        normalized: Its :func:`_normalize` form, passed in rather than recomputed.

    Returns:
        True for a member of :data:`COUNT_WORDS` and for a short bare integer.
    """
    if normalized in COUNT_WORDS:
        return True
    stripped = token.strip(_EDGE_PUNCTUATION)
    return stripped.isdigit() and len(stripped) <= MAX_DIGIT_RUN


def aggregate_count_phrases(text: str) -> tuple[str, ...]:
    """Every place TEXT restates the size of the published route set.

    Whitespace is normalized across lines before anything is matched, which is
    the load-bearing part: the sentence CS-927 removed wrapped mid-phrase, so a
    line-oriented scan reads the halves as unrelated and finds nothing.

    Args:
        text: The prose to scan.

    Returns:
        The offending count-and-noun phrases in their ORIGINAL spelling, one per
        hit, so a failure names what to go and read rather than only how many.
    """
    original = text.split()
    normalized = tuple(_normalize(token) for token in original)
    hits: list[str] = []
    for index, token in enumerate(original):
        if not _is_count(token, normalized[index]):
            continue
        noun_at = None
        for offset in range(index + 1, min(index + 1 + NOUN_LOOKAHEAD, len(normalized))):
            if normalized[offset] in AGGREGATE_NOUNS:
                noun_at = offset
                break
        if noun_at is None:
            continue
        if noun_at + 1 < len(normalized) and normalized[noun_at + 1] == DISTRIBUTIVE_WORD:
            continue
        before = normalized[max(0, index - AUTHORITY_SPAN) : index]
        after = normalized[noun_at + 1 : noun_at + 1 + AUTHORITY_SPAN]
        if any(word in AUTHORITY_TOKENS for word in before + after):
            hits.append(" ".join(original[index : noun_at + 1]))
    return tuple(hits)


def population_files() -> tuple[Path, ...]:
    """Every file under the shipping package whose prose this guard grades.

    Returns:
        Absolute paths, sorted, read from the filesystem rather than from git so
        an untracked module cannot be green here and red at commit time.
    """
    root = REPO_ROOT / POPULATION_ROOT_RELATIVE
    found = [
        path for path in root.rglob("*") if path.is_file() and path.suffix in POPULATION_SUFFIXES
    ]
    return tuple(sorted(found))


# ---------------------------------------------------------------------------
# Each vocabulary's MEMBERSHIP is pinned in both directions, against a literal
# authored separately below. An arm PARAMETRIZED over a vocabulary cannot do
# this job: deleting a member deletes that member's own arm, so the suite stays
# green. Measured, not feared - a mutation dropping "eleven" from COUNT_WORDS
# survived the first pass of this module with 143 arms green and none red.
# ---------------------------------------------------------------------------


def test_the_count_vocabulary_membership_is_pinned_in_both_directions() -> None:
    expected = (
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
        "eleven",
        "twelve",
        "thirteen",
        "fourteen",
        "fifteen",
        "sixteen",
        "seventeen",
        "eighteen",
        "nineteen",
        "twenty",
    )
    missing = sorted(frozenset(expected) - frozenset(COUNT_WORDS))
    extra = sorted(frozenset(COUNT_WORDS) - frozenset(expected))
    drift_count = len(missing) + len(extra)
    assert drift_count == 0, (
        f"COUNT_WORDS drifted: {len(missing)} missing {missing}, {len(extra)} extra {extra}"
    )


def test_the_aggregate_noun_vocabulary_membership_is_pinned_in_both_directions() -> None:
    expected = ("endpoint", "endpoints", "route", "routes", "template", "templates")
    missing = sorted(frozenset(expected) - frozenset(AGGREGATE_NOUNS))
    extra = sorted(frozenset(AGGREGATE_NOUNS) - frozenset(expected))
    drift_count = len(missing) + len(extra)
    assert drift_count == 0, (
        f"AGGREGATE_NOUNS drifted: {len(missing)} missing {missing}, {len(extra)} extra {extra}"
    )


def test_the_authority_vocabulary_membership_is_pinned_in_both_directions() -> None:
    expected = ("bootstrapmd", "section")
    missing = sorted(frozenset(expected) - frozenset(AUTHORITY_TOKENS))
    extra = sorted(frozenset(AUTHORITY_TOKENS) - frozenset(expected))
    drift_count = len(missing) + len(extra)
    assert drift_count == 0, (
        f"AUTHORITY_TOKENS drifted: {len(missing)} missing {missing}, {len(extra)} extra {extra}"
    )


def test_every_authority_token_has_a_plant_that_isolates_it() -> None:
    planted = sorted(AUTHORITY_PLANTS)
    declared = sorted(AUTHORITY_TOKENS)
    unplanted = sorted(frozenset(declared) - frozenset(planted))
    unplanted_count = len(unplanted)
    assert unplanted_count == 0, (
        f"{unplanted_count} authority token(s) have no isolating plant: {unplanted}"
    )


@pytest.mark.parametrize("token", AUTHORITY_TOKENS)
def test_each_authority_token_carries_a_hit_on_its_own(token: str) -> None:
    """Each member is load-bearing alone, not only as half of the usual pair."""
    planted = AUTHORITY_PLANTS[token]
    normalized = frozenset(_normalize(word) for word in planted.split())
    companions = sorted(normalized & frozenset(AUTHORITY_TOKENS) - {token})
    companion_count = len(companions)
    assert companion_count == 0, (
        f"the plant for {token} also carries {companion_count} other authority "
        f"token(s) {companions}, so it does not isolate {token}"
    )
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 1, f"the detector did not fire on {token} standing alone"


# ---------------------------------------------------------------------------
# The detector is graded BEFORE it is trusted. "Found no problems" and "looks
# for no problems" are otherwise the same output (CONVENTIONS.md section 7.2).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("word", COUNT_WORDS)
@pytest.mark.parametrize("noun", AGGREGATE_NOUNS)
def test_the_detector_fires_on_every_word_and_noun_in_its_vocabulary(word: str, noun: str) -> None:
    planted = f"are two of the {word} {noun} ``BOOTSTRAP.md`` section 7.1 publishes"
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 1, f"the detector did not fire on a planted pair: {word} {noun}"


def test_the_detector_fires_on_a_digit_count() -> None:
    planted = "the 11 endpoints ``BOOTSTRAP.md`` section 7.1 publishes"
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 1, "the detector missed a count spelled in digits"


def test_the_detector_fires_on_the_stale_sentence_this_item_removed() -> None:
    """The plant wraps mid-phrase, which is the shape a line-based scan misses."""
    planted = (
        "The cost of the refusal was not theoretical - ``/api/advice/<id>/derivation`` and\n"
        "``/api/advice/<id>/state`` are two of the nine endpoints ``BOOTSTRAP.md`` section\n"
        "7.1 publishes, ``contract.ENDPOINT_PATTERN`` already admitted their spelling"
    )
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 1, "the detector missed the wrapped sentence CS-929 removed"


def test_the_detector_fires_when_the_authority_leads_instead_of_trails() -> None:
    """The clause order ``docs/adr/0012`` uses. A one-sided window reads it clean."""
    planted = "``BOOTSTRAP.md`` section 7.1 names nine endpoints. Four of them have a layer"
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 1, "the detector missed the shape with the authority leading"


def test_a_correct_value_restatement_reddens_the_guard() -> None:
    """CS-933 entire: the shape is the population, and the value is never consulted.

    The planted count is read from the OWNER at run time, so this plant is
    literally correct today and stays correct as the set grows. A value sweep
    would pass it. This guard must not.
    """
    published_count = len(health.ENDPOINT_TEMPLATES)
    vocabulary_size = len(COUNT_WORDS)
    assert 0 < published_count <= vocabulary_size, (
        "the published set is empty or larger than this guard can spell, so the "
        "correct-value plant cannot be constructed and this arm would prove nothing"
    )
    word = COUNT_WORDS[published_count - 1]
    planted = f"The {word} routes ``BOOTSTRAP.md`` section 7.1 publishes, in that order"
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 1, (
        "a restatement carrying the CURRENT correct count did not redden the guard, "
        "which makes this a value sweep and reproduces the defect CS-933 was filed for"
    )


def test_the_detector_fires_on_the_sentence_cs933_was_filed_against() -> None:
    """Lifted from ``app.js`` as CS-933 filed it. Correct then, and still in scope."""
    planted = "The ten routes BOOTSTRAP.md section 7.1 publishes, in that section's order"
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 1, "the detector missed the app.js sentence CS-933 was filed against"


def test_the_detector_fires_on_the_sentence_cs927_removed() -> None:
    planted = "is asserted to hold exactly the nine templates ``BOOTSTRAP.md`` section 7.1 names"
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 1, "the detector missed the pending.py sentence CS-927 removed"


# ---------------------------------------------------------------------------
# The boundary is pinned in the OTHER direction too. A guard that reddens on a
# module counting its own subset is a wrong guard, not a strict one.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "legal",
    [
        "The five endpoints whose computing layer does not exist yet, answering so.",
        "The five unbacked endpoints, one route each, ready to be registered.",
        "The five routes, in a stable order, with pairwise distinct templates.",
        "naming a different item on each would imply five independent unlocks",
    ],
)
def test_the_detector_leaves_a_modules_own_subset_count_alone(legal: str) -> None:
    """Lifted verbatim from ``pending.py``, which OWNS the number five."""
    hit_count = len(aggregate_count_phrases(legal))
    assert hit_count == 0, "the detector fired on a module counting its own subset"


@pytest.mark.parametrize(
    "distributive",
    [
        "One route per published template, in ``BOOTSTRAP.md`` section 7.1's order.",
        "Assemble one route per published template, with the providers bound in.",
        "ONE ROUTE PER TEMPLATE, AND THE METHOD-BOUNDARY ROUTE IS PUBLISHED",
    ],
)
def test_the_detector_does_not_read_a_distributive_phrase_as_a_count(
    distributive: str,
) -> None:
    """A rate is not a count. Lifted from ``routes.py`` and ``pending.py``."""
    hit_count = len(aggregate_count_phrases(distributive))
    assert hit_count == 0, "the detector read a distributive phrase as a count"


def test_the_detector_does_not_read_a_section_reference_as_a_count() -> None:
    """``7.1`` keeps its interior dot, so it never reduces to bare digits."""
    hit_count = len(aggregate_count_phrases("``BOOTSTRAP.md`` section 7.1 publishes routes"))
    assert hit_count == 0, "the detector read a section reference as a count"


def test_the_detector_does_not_fire_on_a_bare_aggregate_noun() -> None:
    hit_count = len(aggregate_count_phrases("the templates ``BOOTSTRAP.md`` section 7.1 names"))
    assert hit_count == 0, "the detector fired on a noun with no count in front of it"


def test_the_detector_does_not_fire_on_a_count_with_no_authority_beside_it() -> None:
    """Lifted from ``audit_harness.py``, which records history rather than claiming it.

    This is the arm that shows the authority leg is load-bearing: remove it and
    every legal subset sentence above turns red.
    """
    planted = 'it read "four" from nine templates until CS-912 published a tenth'
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 0, "the detector fired on a count with no authority reference beside it"


def test_the_detector_does_not_fire_when_the_count_is_too_far_from_the_noun() -> None:
    """The repaired ``server.py`` phrasing. Widening the lookahead would break it."""
    planted = "are two of the endpoints ``BOOTSTRAP.md`` section 7.1 publishes"
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 0, "the detector counted the pair under discussion as the aggregate"


# ---------------------------------------------------------------------------
# The population is real. A glob that matched nothing would make the arm this
# item exists for pass by measuring nothing at all.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "relative",
    [
        "clockspeed/surface/server.py",
        "clockspeed/surface/api/health.py",
        "clockspeed/surface/api/pending.py",
        "clockspeed/surface/api/routes.py",
        "clockspeed/surface/web/app.js",
        "clockspeed/surface/web/index.html",
    ],
)
def test_the_population_contains_every_known_carrier(relative: str) -> None:
    members = {path.relative_to(REPO_ROOT).as_posix() for path in population_files()}
    assert relative in members, f"the population does not reach a known carrier: {relative}"


@pytest.mark.parametrize("suffix", POPULATION_SUFFIXES)
def test_the_population_holds_at_least_one_file_of_every_graded_suffix(suffix: str) -> None:
    matched_count = len([path for path in population_files() if path.suffix == suffix])
    assert matched_count > 0, f"the population matched no {suffix} file, so it grades none"


def test_the_population_excludes_the_adr_directory() -> None:
    """Fence: an ADR records what was decided WHEN it was decided."""
    strays = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in population_files()
        if "docs/adr/" in path.relative_to(REPO_ROOT).as_posix()
    )
    stray_count = len(strays)
    assert stray_count == 0, f"the population reached {stray_count} ADR file(s): {strays}"


def test_the_excluded_adr_would_redden_this_guard() -> None:
    """The control that makes the exclusion above a decision rather than a typo.

    If the excluded file carried no hit, "excluded" and "misspelled" would be the
    same observation and the fence would be documenting nothing.
    """
    adr = REPO_ROOT / EXCLUDED_ADR_RELATIVE
    assert adr.is_file(), f"the excluded ADR is not where this fence says it is: {adr.name}"
    hit_count = len(aggregate_count_phrases(adr.read_text(encoding="utf-8", errors="replace")))
    assert hit_count > 0, (
        "the deliberately excluded ADR carries no aggregate count, so the exclusion "
        "proves nothing and either the fence or this control is out of date"
    )


# ---------------------------------------------------------------------------
# The arm this item exists for.
# ---------------------------------------------------------------------------


def test_no_shipping_module_restates_the_published_route_count() -> None:
    offenders = []
    for path in population_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        offenders.extend(
            (path.relative_to(REPO_ROOT).as_posix(), phrase)
            for phrase in aggregate_count_phrases(text)
        )
    offender_count = len(offenders)
    assert offender_count == 0, (
        f"{offender_count} place(s) under {POPULATION_ROOT_RELATIVE}/ restate the size of "
        f"the published route set - {offenders} - and the owner of that number is "
        "health.ENDPOINT_TEMPLATES, not a docstring or a comment"
    )
