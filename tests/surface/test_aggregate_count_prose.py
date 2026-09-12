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
graded here is: A COUNT, of a noun naming the published route set, standing near
a reference to the AUTHORITY that publishes it, with no owner named and no guard
behind it. The value is never consulted.
:func:`test_a_correct_value_restatement_reddens_the_guard` is the arm that
separates this from a value sweep, and without it this module would be the thing
CS-933 exists to prevent.

THE AUTHORITY LEG IS WHAT KEEPS A LEGAL SUBSET LEGAL, and it is load-bearing
rather than decorative. ``pending.py`` says "the five unbacked endpoints" about
its OWN set, and that is a fact it owns; ``audit_harness.py`` says "it read
'four' from nine templates" as a historical record. Neither stands near
``BOOTSTRAP.md`` or a section reference, so neither fires. Both directions are
pinned by their own arms, because a guard that reddens on a module counting its
own subset is a wrong guard, not a strict one.

THE AUTHORITY MAY SIT ON EITHER SIDE, and that too was measured rather than
assumed. ``docs/adr/0012`` spells the same defect with the clauses reversed -
"``BOOTSTRAP.md`` section 7.1 names nine endpoints" - so a detector that only
looked AFTER the noun would read that shape as clean. The window spans both
directions and an arm plants each order.

EVERY KNOB IS PINNED IN BOTH DIRECTIONS, and that is not a style preference. A
knob with an arm only on the tightening side has an UNGRADED let-through
direction: an adversarial pass over the first version of this module found six
surviving mutants, five of them let-throughs, because :data:`NOUN_LOOKAHEAD`,
:data:`AUTHORITY_SPAN`, :data:`MAX_DIGIT_RUN` and the population root could all
be loosened or narrowed with 155 arms staying green. So each of those knobs now
carries two arms: one that dies when it is narrowed, one that dies when it is
widened. Where a live file supplies the widening arm, it is ALSO written here as
a literal, so the boundary survives that file being rewritten. Two more
survivors fell out of the repair round itself and both are worth the reader's
time: a limit plant meant to sit ONE token outside the span actually sat three
outside, so it could not die when the span was widened by one - which is why
:func:`test_an_authority_further_away_than_the_span_is_a_stated_limit` now
measures its own plant's distance before asserting anything - and the breadth
ANCHOR turned out to be a knob of its own, narrowable to ``clockspeed/surface``
with every breadth arm green, so the anchor is now derived from the import
system rather than compared against a literal.

THE POPULATION'S BREADTH IS GUARDED STRUCTURALLY, NOT BY A LIST OF FILENAMES.
The worst of those six survivors moved the population root from ``clockspeed`` to
``clockspeed/surface`` and dropped 28 of 49 files - every module under ``data/``,
``save/``, ``solve/``, ``audit/``, ``progress/`` and ``advisor/`` - with nothing
red, because every named-carrier arm named a file under ``surface/``. So breadth
is now derived: :func:`test_the_population_covers_every_shipping_package` lists
the package directories under ``clockspeed/`` from the filesystem and requires
each to contribute, and
:func:`test_the_population_is_a_superset_of_the_anchored_corpus` re-derives the
whole corpus from anchors spelled independently of the knob. Adding a package
cannot go unswept either.

THE ELECTRON SHELL IS IN THE POPULATION. ``shell/`` carries 18 ``.js`` files and
is the companion surface that renders the same route set, so a restated count
there is the same defect in a different language; it was measured to carry none
today, which is why including it costs nothing. Its ``test/`` subtree is excluded
on the same terms as ``tests/``.

WHAT IS OUT OF POPULATION, stated as a decision rather than left to a glob.
``docs/adr/`` is excluded ON PURPOSE. An ADR records what was decided WHEN it was
decided; correcting ``docs/adr/0012`` would rewrite history rather than fix
drift, and CS-929's note refuses it in so many words. That exclusion is not a
typo dressed as a policy: :func:`test_the_excluded_adr_would_redden_this_guard`
proves the excluded file DOES carry the shape. ``BOOTSTRAP.md`` section 7.1 is
likewise out - it is the document that ENUMERATES the set, so it is the one place
a size may be spelled - and so are ``tests/`` and ``docs/`` generally, which
RECORD the history of these sentences on purpose. Running this detector over
``docs/`` fires on ``docs/ARCHITECTURE.md``'s "The five endpoints that would
surface it", a legal subset count that only looks like an aggregate because an
authority reference happens to sit six tokens back. That is information about the
heuristic's limit, not a site to edit.

WHAT THIS DETECTOR CANNOT CATCH, stated here rather than left for the next
adversary to find. Each of these was planted, measured to pass through, and has
an arm below pinning the boundary so it cannot move silently.

  - A COUNT SEPARATED FROM ITS NOUN BY TWO OR MORE MODIFIERS - "the eleven
    distinct HTTP endpoints". This one is not a tuning oversight and cannot be
    fixed by widening: ``clockspeed/surface/api/solve.py`` line 3 says "the
    request grammar for the two backed solver endpoints" about the two endpoints
    it OWNS, under the house opener "Owns (BOOTSTRAP.md section 7.1):" that puts
    an authority reference beside every count in every module's first sentence.
    The two shapes are lexically identical; the only discriminator is the VALUE,
    and keying on the value is exactly the defect CS-933 forbids. Measured: at a
    lookahead of three the population reddens on that legal sentence AND on this
    item's own repair, both live files.
  - A COUNT MORE THAN :data:`NOUN_LOOKBEHIND` TOKENS BEFORE ITS NOUN - "the
    endpoints are listed, eleven in all".
  - AN AUTHORITY REFERENCE MORE THAN :data:`AUTHORITY_SPAN` TOKENS AWAY. The span
    is the dial that trades reach against subset false positives, and it is set
    at the widest value the measured population tolerates: at 12 it reddens
    ``pending.py``'s own legal "five unbacked endpoints".
  - A COMPOUND JOINED BY ANYTHING BUT A HYPHEN. ``route-templates`` is split and
    caught; ``route_templates`` is not, and deliberately - splitting on the
    underscore would make ``ENDPOINT_TEMPLATES`` yield the token "templates",
    so the sentences that correctly NAME the owner would start reddening.
  - A COUNT SPELLED IN A WAY :data:`COUNT_WORDS` does not hold. "a dozen" and
    "twenty-one" are caught; "a handful" and "a couple" are not counts.

THE SENTENCE-BOUNDARY CASE IS A DELIBERATE DECISION, NOT AN OVERSIGHT. This
detector is a pure PROXIMITY heuristic and does not respect sentence boundaries
at all, so "``BOOTSTRAP.md`` section 7.1 is the owner. There are eleven
endpoints." IS caught, and an arm plants it. That choice is taken knowingly: this
repository's prose routinely puts the authority in one sentence and the claim in
the next, so a boundary-respecting detector would miss the house style. The cost
is the ``docs/ARCHITECTURE.md`` shape above - a subset count near an unrelated
authority reference. Inside the population that cost was measured at ZERO, and
the span is what holds it there.

Test-quality discipline (CONVENTIONS.md section 7.2). Every population size is
bound to a SCALAR before it is asserted, so the pytest assertion channel renders
an integer rather than the collection behind it (CS-850). The population is read
from the FILESYSTEM rather than from ``git ls-files``, so an untracked module
cannot be green here and red at commit time. Nothing rendered here is a path from
this machine - the paths are repository-relative and the phrases are literals
authored in this repository or lifted from a tracked source file.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Final

import pytest

from clockspeed.surface.api import health, pending, solve

# ---------------------------------------------------------------------------
# The detector
# ---------------------------------------------------------------------------

REPO_ROOT: Final = Path(__file__).resolve().parents[2]

#: Spelled number words this guard reads as a count. Membership is pinned in
#: both directions below against a literal authored separately, because an arm
#: PARAMETRIZED over a vocabulary cannot grade the vocabulary: deleting a member
#: deletes that member's own arm. Deliberately NOT shared with
#: ``tools/drift_guard.py``'s duration vocabulary, for the reason
#: ``test_pending_route_count.py`` already states.
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
    "dozen",
)

#: The nouns that name the PUBLISHED ROUTE SET. Three spellings appear in this
#: repository's prose for the same set - "endpoints" in ``server.py``, "routes"
#: in ``app.js``, "templates" in ``pending.py`` - which is how CS-929 and CS-933
#: came to be two items instead of none. The remaining six were planted by an
#: adversarial pass and measured to pass through the first version of this
#: module, so they are here by measurement rather than by imagination.
AGGREGATE_NOUNS: Final = (
    "endpoint",
    "endpoints",
    "route",
    "routes",
    "template",
    "templates",
    "path",
    "paths",
    "url",
    "urls",
    "handler",
    "handlers",
    "api",
    "apis",
    "resource",
    "resources",
    "surface",
    "surfaces",
)

#: A reference to WHO PUBLISHES the set. Its presence is what makes a count an
#: AGGREGATE count rather than a module counting its own subset, and its absence
#: is why "the five unbacked endpoints" stays legal. "specification", "spec" and
#: bare "bootstrap" are here because ``CLAUDE.md`` itself calls ``BOOTSTRAP.md``
#: "the project specification", so those are house spellings rather than
#: contrived ones. ``BOOTSTRAP.md`` normalizes to "bootstrapmd", which is why
#: both it and bare "bootstrap" are needed.
AUTHORITY_TOKENS: Final = (
    "bootstrapmd",
    "bootstrap",
    "section",
    "specification",
    "spec",
)

#: One plant per authority token, each carrying THAT TOKEN AND NO OTHER. Every
#: real carrier in this repository names two at once - "``BOOTSTRAP.md`` section
#: 7.1" - so a suite that only ever plants the pair leaves each member
#: individually unmeasured: a mutation deleting "bootstrapmd" survived the first
#: pass of this module with all arms green, because "section" carried every
#: plant on its own.
AUTHORITY_PLANTS: Final = {
    "bootstrapmd": "the nine endpoints ``BOOTSTRAP.md`` publishes",
    "bootstrap": "the nine endpoints BOOTSTRAP publishes",
    "section": "the nine endpoints section 7.1 publishes",
    "specification": "the nine endpoints the project specification publishes",
    "spec": "the nine endpoints the spec publishes",
}

#: How many tokens may sit between the count and the noun. TWO, and this is the
#: one knob whose value is forced rather than chosen: at three the population
#: reddens on ``solve.py``'s legal "two backed solver endpoints" and on this
#: item's own repair, and the module docstring's limits section explains why no
#: value can separate those from "the eleven distinct HTTP endpoints".
NOUN_LOOKAHEAD: Final = 2

#: How many tokens the noun may sit BEFORE the count - "the endpoints (eleven)",
#: "the endpoints, all eleven". Both directions pinned by their own arms.
NOUN_LOOKBEHIND: Final = 2

#: How far either side of the count-noun pair an authority reference is still
#: read as attached to it. EIGHT: enough to reach "published by this module, as
#: enumerated in ``BOOTSTRAP.md`` section 7.1", and short enough that the
#: measured population carries no hit. At twelve ``pending.py`` reddens.
AUTHORITY_SPAN: Final = 8

#: A noun followed by this is distributive - a RATE, not a count. "One route per
#: published template" states a one-to-one correspondence and must never fire;
#: ``routes.py`` says it three times and ``pending.py`` once.
DISTRIBUTIVE_WORD: Final = "per"

#: Longest run of digits read as a count. THREE, so "100" counts and a year does
#: not. Only a BARE digit token qualifies, which is what keeps a numbered-list
#: marker ("10)") and a section reference ("7.1") out; both have their own arm.
MAX_DIGIT_RUN: Final = 3

#: Split on this before tokenizing, so ``route-templates`` reads as two tokens
#: and ``twenty-one`` as a count. The underscore is deliberately NOT split - see
#: the docstring's limits section.
COMPOUND_SEPARATOR: Final = "-"

#: Which file suffixes carry prose this guard grades.
POPULATION_SUFFIXES: Final = (".py", ".js", ".html")

#: Where the population is rooted: the shipping Python package and the Electron
#: shell. Breadth is NOT trusted to this knob - the arms below re-derive the
#: corpus from anchors spelled independently of it.
POPULATION_ROOTS: Final = ("clockspeed", "shell")

#: Path components that take a file out of the population wherever they appear.
#: Test trees RECORD the history of these sentences on purpose.
EXCLUDED_PATH_PARTS: Final = ("__pycache__", "node_modules", "test", "tests")

#: Directories that must never contribute, asserted rather than assumed. These
#: are the deliberate exclusions the docstring argues for, and the arm over them
#: is what dies if the population root is widened toward the repository root.
FORBIDDEN_POPULATION_PREFIXES: Final = (
    "tests/",
    "docs/",
    "tools/",
    "ops/",
    "scripts/",
    "memory/",
)

#: The ADR that spells this defect and is deliberately left alone.
EXCLUDED_ADR_RELATIVE: Final = "docs/adr/0012-dashboard-refusal-vocabulary-and-wire-form.md"

#: The package anchor, spelled here so the breadth arms cannot drift with the
#: knob they are grading.
SHIPPING_PACKAGE_ANCHOR: Final = "clockspeed"

#: The Electron shell anchor, on the same terms.
SHELL_ANCHOR: Final = "shell"


def _normalize(token: str) -> str:
    """Reduce one whitespace-separated token to its lowercase letters.

    Args:
        token: A single token in its original spelling.

    Returns:
        The token's letters, lowercased. A token with no letters reduces to the
        empty string and can therefore never match either vocabulary.
    """
    return "".join(character for character in token if character.isalpha()).lower()


def _tokenize(text: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Split TEXT into index-aligned original and normalized token runs.

    Whitespace is normalized across lines before anything is matched, which is
    the load-bearing part: the sentence CS-927 removed wrapped mid-phrase, so a
    line-oriented scan reads the halves as unrelated and finds nothing. The
    compound separator is turned into whitespace first, so a hyphenated compound
    contributes its parts rather than one fused token.

    Args:
        text: The prose to tokenize.

    Returns:
        The original tokens and their normalized forms, same length, same order.
    """
    original = tuple(text.replace(COMPOUND_SEPARATOR, " ").split())
    return original, tuple(_normalize(token) for token in original)


def _is_count(token: str, normalized: str) -> bool:
    """Whether TOKEN spells a count, as a word or as a bare digit run.

    Args:
        token: The token in its original spelling, punctuation included.
        normalized: Its :func:`_normalize` form, passed in rather than recomputed.

    Returns:
        True for a member of :data:`COUNT_WORDS`, and for a bare run of at most
        :data:`MAX_DIGIT_RUN` digits. "10)" and "7.1" are not bare and so are
        not counts.
    """
    if normalized in COUNT_WORDS:
        return True
    return token.isdigit() and len(token) <= MAX_DIGIT_RUN


def _noun_index(normalized: tuple[str, ...], index: int) -> int | None:
    """Where the aggregate noun paired with the count at INDEX sits, if anywhere.

    Args:
        normalized: The normalized token run.
        index: Position of the count token.

    Returns:
        The noun's index, searching forward first and then backward, or None.
    """
    for offset in range(index + 1, min(index + 1 + NOUN_LOOKAHEAD, len(normalized))):
        if normalized[offset] in AGGREGATE_NOUNS:
            return offset
    for offset in range(index - 1, max(-1, index - 1 - NOUN_LOOKBEHIND), -1):
        if normalized[offset] in AGGREGATE_NOUNS:
            return offset
    return None


def aggregate_count_phrases(text: str) -> tuple[str, ...]:
    """Every place TEXT restates the size of the published route set.

    Args:
        text: The prose to scan.

    Returns:
        The offending count-and-noun phrases in their ORIGINAL spelling, one per
        hit, so a failure names what to go and read rather than only how many.
    """
    original, normalized = _tokenize(text)
    hits: list[str] = []
    for index, token in enumerate(original):
        if not _is_count(token, normalized[index]):
            continue
        noun_at = _noun_index(normalized, index)
        if noun_at is None:
            continue
        if noun_at + 1 < len(normalized) and normalized[noun_at + 1] == DISTRIBUTIVE_WORD:
            continue
        low = min(index, noun_at)
        high = max(index, noun_at)
        window = (
            normalized[max(0, low - AUTHORITY_SPAN) : low]
            + normalized[high + 1 : high + 1 + AUTHORITY_SPAN]
        )
        if any(word in AUTHORITY_TOKENS for word in window):
            hits.append(" ".join(original[low : high + 1]))
    return tuple(hits)


def _is_population_member(path: Path) -> bool:
    """Whether PATH is a file this guard grades.

    Args:
        path: A candidate path.

    Returns:
        True for a regular file with a graded suffix and no excluded component.
    """
    return (
        path.is_file()
        and path.suffix in POPULATION_SUFFIXES
        and not any(part in EXCLUDED_PATH_PARTS for part in path.parts)
    )


def population_files() -> tuple[Path, ...]:
    """Every file whose prose this guard grades.

    Returns:
        Absolute paths, sorted and de-duplicated, read from the filesystem
        rather than from git so an untracked module cannot be green here and red
        at commit time.
    """
    found: set[Path] = set()
    for root in POPULATION_ROOTS:
        found.update(path for path in (REPO_ROOT / root).rglob("*") if _is_population_member(path))
    return tuple(sorted(found))


def _anchored_corpus() -> tuple[Path, ...]:
    """The corpus re-derived from anchors spelled independently of the knob.

    This exists so narrowing :data:`POPULATION_ROOTS` cannot silently shrink what
    is graded. It repeats the suffix and exclusion logic on purpose: a guard that
    derives its expectation from the value it is grading grades nothing.

    Returns:
        Absolute paths, sorted.
    """
    found: set[Path] = set()
    for anchor in (SHIPPING_PACKAGE_ANCHOR, SHELL_ANCHOR):
        for path in (REPO_ROOT / anchor).rglob("*"):
            if not path.is_file() or path.suffix not in (".py", ".js", ".html"):
                continue
            if any(part in ("__pycache__", "node_modules", "test", "tests") for part in path.parts):
                continue
            found.add(path)
    return tuple(sorted(found))


def _relative(paths: object) -> list[str]:
    """Repository-relative spellings, for a failure message.

    Args:
        paths: An iterable of absolute paths under :data:`REPO_ROOT`.

    Returns:
        Sorted posix-style relative paths.
    """
    return sorted(path.relative_to(REPO_ROOT).as_posix() for path in paths)  # type: ignore[attr-defined]


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
        "dozen",
    )
    missing = sorted(frozenset(expected) - frozenset(COUNT_WORDS))
    extra = sorted(frozenset(COUNT_WORDS) - frozenset(expected))
    drift_count = len(missing) + len(extra)
    assert drift_count == 0, (
        f"COUNT_WORDS drifted: {len(missing)} missing {missing}, {len(extra)} extra {extra}"
    )


def test_the_aggregate_noun_vocabulary_membership_is_pinned_in_both_directions() -> None:
    expected = (
        "endpoint",
        "endpoints",
        "route",
        "routes",
        "template",
        "templates",
        "path",
        "paths",
        "url",
        "urls",
        "handler",
        "handlers",
        "api",
        "apis",
        "resource",
        "resources",
        "surface",
        "surfaces",
    )
    missing = sorted(frozenset(expected) - frozenset(AGGREGATE_NOUNS))
    extra = sorted(frozenset(AGGREGATE_NOUNS) - frozenset(expected))
    drift_count = len(missing) + len(extra)
    assert drift_count == 0, (
        f"AGGREGATE_NOUNS drifted: {len(missing)} missing {missing}, {len(extra)} extra {extra}"
    )


def test_the_authority_vocabulary_membership_is_pinned_in_both_directions() -> None:
    expected = ("bootstrapmd", "bootstrap", "section", "specification", "spec")
    missing = sorted(frozenset(expected) - frozenset(AUTHORITY_TOKENS))
    extra = sorted(frozenset(AUTHORITY_TOKENS) - frozenset(expected))
    drift_count = len(missing) + len(extra)
    assert drift_count == 0, (
        f"AUTHORITY_TOKENS drifted: {len(missing)} missing {missing}, {len(extra)} extra {extra}"
    )


def test_the_excluded_path_component_membership_is_pinned_in_both_directions() -> None:
    expected = ("__pycache__", "node_modules", "test", "tests")
    missing = sorted(frozenset(expected) - frozenset(EXCLUDED_PATH_PARTS))
    extra = sorted(frozenset(EXCLUDED_PATH_PARTS) - frozenset(expected))
    drift_count = len(missing) + len(extra)
    assert drift_count == 0, (
        f"EXCLUDED_PATH_PARTS drifted: {len(missing)} missing {missing}, {len(extra)} extra {extra}"
    )


def test_the_forbidden_prefix_membership_is_pinned_in_both_directions() -> None:
    expected = ("tests/", "docs/", "tools/", "ops/", "scripts/", "memory/")
    missing = sorted(frozenset(expected) - frozenset(FORBIDDEN_POPULATION_PREFIXES))
    extra = sorted(frozenset(FORBIDDEN_POPULATION_PREFIXES) - frozenset(expected))
    drift_count = len(missing) + len(extra)
    assert drift_count == 0, (
        f"FORBIDDEN_POPULATION_PREFIXES drifted: {len(missing)} missing {missing}, "
        f"{len(extra)} extra {extra}"
    )


def test_the_population_suffix_membership_is_pinned_in_both_directions() -> None:
    expected = (".py", ".js", ".html")
    missing = sorted(frozenset(expected) - frozenset(POPULATION_SUFFIXES))
    extra = sorted(frozenset(POPULATION_SUFFIXES) - frozenset(expected))
    drift_count = len(missing) + len(extra)
    assert drift_count == 0, (
        f"POPULATION_SUFFIXES drifted: {len(missing)} missing {missing}, {len(extra)} extra {extra}"
    )


def test_every_authority_token_has_a_plant_that_isolates_it() -> None:
    unplanted = sorted(frozenset(AUTHORITY_TOKENS) - frozenset(AUTHORITY_PLANTS))
    unplanted_count = len(unplanted)
    assert unplanted_count == 0, (
        f"{unplanted_count} authority token(s) have no isolating plant: {unplanted}"
    )


@pytest.mark.parametrize("token", AUTHORITY_TOKENS)
def test_each_authority_token_carries_a_hit_on_its_own(token: str) -> None:
    """Each member is load-bearing alone, not only as half of the usual pair."""
    planted = AUTHORITY_PLANTS[token]
    _original, normalized = _tokenize(planted)
    companions = sorted((frozenset(normalized) & frozenset(AUTHORITY_TOKENS)) - {token})
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
    planted = f"the {word} {noun} ``BOOTSTRAP.md`` section 7.1 publishes"
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 1, f"the detector did not fire on a planted pair: {word} {noun}"


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
    assert hit_count > 0, "the detector missed the shape with the authority leading"


def test_the_detector_fires_across_a_sentence_boundary() -> None:
    """A DELIBERATE decision, argued in the module docstring, not an accident.

    The detector is a pure proximity heuristic. This repository's prose routinely
    puts the authority in one sentence and the claim in the next, so respecting
    sentence boundaries would miss the house style; the cost is stated above.
    """
    planted = "  ``BOOTSTRAP.md`` section 7.1 is the owner. There are eleven endpoints."
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 1, "the detector missed a count split from its authority by a full stop"


def test_the_detector_fires_on_a_hyphenated_compound() -> None:
    """``server.py`` already writes "route templates" unhyphenated, one keystroke away."""
    planted = "the eleven route-templates ``BOOTSTRAP.md`` section 7.1 publishes"
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count > 0, "a hyphen fused the noun to its modifier and hid the count"


def test_the_detector_fires_on_a_hyphenated_count_word() -> None:
    planted = "the twenty-one endpoints ``BOOTSTRAP.md`` section 7.1 publishes"
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count > 0, "a hyphenated count word was not read as a count"


def test_the_detector_fires_when_the_count_follows_the_noun() -> None:
    planted = "the endpoints (eleven) ``BOOTSTRAP.md`` section 7.1 publishes"
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 1, "the detector missed a count parenthesised after its noun"


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
# NOUN_LOOKAHEAD, pinned in BOTH directions.
# ---------------------------------------------------------------------------


def test_the_detector_reaches_a_noun_at_the_full_lookahead() -> None:
    """Dies if NOUN_LOOKAHEAD is narrowed. The noun sits exactly two tokens out."""
    planted = "the eleven published endpoints ``BOOTSTRAP.md`` section 7.1 names"
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 1, "the detector no longer reaches a noun two tokens past the count"


def test_the_detector_leaves_the_live_solve_docstring_alone() -> None:
    """Dies if NOUN_LOOKAHEAD is widened. Lifted from ``solve.py``, which owns TWO.

    This is the arm that makes "the eleven distinct HTTP endpoints" uncatchable
    rather than merely uncaught: the two shapes are lexically identical and the
    only discriminator is the value. The live module is graded too, just below.
    """
    lifted = (
        "Owns (BOOTSTRAP.md section 7.1): the request grammar for the two backed solver\n"
        "endpoints, the JSON spelling of a ``ProductionPlan`` and an ``OptimizeResult``,\n"
        "and the transcription of a solver refusal into the frozen envelope."
    )
    hit_count = len(aggregate_count_phrases(lifted))
    assert hit_count == 0, (
        "the detector read a module's count of the endpoints it OWNS as an aggregate "
        "restatement, which makes every 'Owns (BOOTSTRAP.md section 7.1):' opener a "
        "false positive"
    )


def test_the_detector_leaves_the_repaired_server_sentence_alone() -> None:
    """Dies if NOUN_LOOKAHEAD is widened. This item's own repair, as a literal."""
    lifted = (
        "``/api/advice/<id>/state`` are two of the endpoints ``BOOTSTRAP.md`` section 7.1\n"
        "publishes, and HOW MANY IT PUBLISHES IS NOT WRITTEN DOWN HERE: that number is\n"
        "owned by ``api.health.ENDPOINT_TEMPLATES``"
    )
    hit_count = len(aggregate_count_phrases(lifted))
    assert hit_count == 0, (
        "the detector read 'two of the endpoints' - a count of the PAIR under "
        "discussion - as a count of the published set"
    )


@pytest.mark.parametrize("module", [pending, solve])
def test_the_live_subset_counting_modules_stay_green(module: object) -> None:
    """The real files behind the two literals above, graded as they ship."""
    phrases = aggregate_count_phrases(inspect.getsource(module))  # type: ignore[arg-type]
    phrase_count = len(phrases)
    assert phrase_count == 0, (
        f"a module counting its own subset reddened in {phrase_count} place(s): {list(phrases)}"
    )


# ---------------------------------------------------------------------------
# NOUN_LOOKBEHIND, pinned in BOTH directions.
# ---------------------------------------------------------------------------


def test_the_detector_reaches_a_noun_at_the_full_lookbehind() -> None:
    """Dies if NOUN_LOOKBEHIND is narrowed. The noun sits exactly two tokens back."""
    planted = "the endpoints, all eleven, ``BOOTSTRAP.md`` section 7.1 publishes"
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 1, "the detector no longer reaches a noun two tokens before the count"


def test_a_noun_further_back_than_the_lookbehind_is_a_stated_limit() -> None:
    """Dies if NOUN_LOOKBEHIND is widened. NOT a claim that this shape is benign.

    It is the defect, spelled at a distance this detector does not reach. The arm
    exists so the boundary cannot move without a decision, and the module
    docstring lists the shape among what cannot be caught.
    """
    planted = "the endpoints are listed, eleven in all, in ``BOOTSTRAP.md`` section 7.1"
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 0, (
        "the lookbehind now reaches three tokens; if that is intended, the docstring's "
        "limits section and this arm must be rewritten together"
    )


# ---------------------------------------------------------------------------
# AUTHORITY_SPAN, pinned in BOTH directions.
# ---------------------------------------------------------------------------


def test_the_detector_reaches_an_authority_at_the_full_span() -> None:
    """Dies if AUTHORITY_SPAN is narrowed. The authority sits exactly eight tokens out."""
    planted = (
        "the eleven endpoints published by this module, as enumerated in "
        "``BOOTSTRAP.md`` section 7.1"
    )
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 1, "the detector no longer reaches an authority eight tokens away"


def test_an_authority_further_away_than_the_span_is_a_stated_limit() -> None:
    """Dies if AUTHORITY_SPAN is widened. The trade is argued in the docstring.

    Widening the span reaches more real carriers AND more subset false positives;
    at twelve it reddens ``pending.py``'s own legal count, which the live-module
    arm above would then catch.
    """
    planted = (
        "the eleven endpoints published by this module, and as enumerated in "
        "``BOOTSTRAP.md`` section 7.1"
    )
    authority_distance = 9
    _original, normalized = _tokenize(planted)
    noun_at = normalized.index("endpoints")
    offset = min(
        index - noun_at
        for index, word in enumerate(normalized)
        if word in AUTHORITY_TOKENS and index > noun_at
    )
    assert offset == authority_distance, (
        f"this plant puts its authority {offset} tokens past the noun, not "
        f"{authority_distance}, so it does not sit one step outside the span and "
        "would not die when the span is widened by one"
    )
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 0, (
        "the span now reaches nine tokens; if that is intended, re-measure the "
        "population's false positives before widening it further"
    )


# ---------------------------------------------------------------------------
# MAX_DIGIT_RUN, pinned in BOTH directions.
# ---------------------------------------------------------------------------


def test_the_detector_fires_on_a_digit_count_at_the_full_run() -> None:
    """Dies if MAX_DIGIT_RUN is narrowed. Three digits is the stated ceiling."""
    planted = "the 100 endpoints ``BOOTSTRAP.md`` section 7.1 publishes"
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 1, "the detector no longer reads a three-digit run as a count"


def test_a_longer_digit_run_is_not_a_count() -> None:
    """Dies if MAX_DIGIT_RUN is widened. A year beside a noun is not a route count."""
    planted = "the 2026 endpoints ``BOOTSTRAP.md`` section 7.1 publishes"
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 0, "a four-digit run was read as a count of the published set"


def test_a_numbered_list_marker_is_not_a_count() -> None:
    """Lifted from the false positive a non-bare digit rule produced in version.py."""
    planted = "item 10). Args: path: the ``BOOTSTRAP.md`` section 7.1 target"
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 0, "a numbered-list marker beside a parameter named path fired"


def test_the_detector_does_not_read_a_section_reference_as_a_count() -> None:
    """``7.1`` is not a bare digit run, so it never reduces to a count."""
    hit_count = len(aggregate_count_phrases("``BOOTSTRAP.md`` section 7.1 publishes routes"))
    assert hit_count == 0, "the detector read a section reference as a count"


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


def test_two_modifiers_between_count_and_noun_is_a_stated_limit() -> None:
    """The shape that CANNOT be caught, pinned so the decision cannot drift silently.

    Identical in structure to ``solve.py``'s legal "two backed solver endpoints";
    the only discriminator is the value, and CS-933 forbids keying on the value.
    If this ever goes red, the two arms above it will have gone red with it.
    """
    planted = "the eleven distinct HTTP endpoints ``BOOTSTRAP.md`` section 7.1 publishes"
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 0, (
        "the detector now reaches a noun three tokens out; re-measure the population "
        "before keeping that, because solve.py's legal subset count fires there"
    )


# ---------------------------------------------------------------------------
# The population is real, and its BREADTH is derived rather than listed. A glob
# that matched nothing - or a root narrowed to one subpackage - would make the
# arm this item exists for pass by measuring almost nothing at all.
# ---------------------------------------------------------------------------


def test_the_shipping_package_anchor_is_the_top_level_package() -> None:
    """The breadth ANCHOR is itself a knob, and an unpinned anchor is an unpinned guard.

    Narrowing the anchor to ``clockspeed/surface`` left every breadth arm green
    while shrinking what they grade to one subpackage - the same defect the
    breadth arms exist to kill, one level up. The expectation is DERIVED from the
    import system rather than written down: the module this suite imports knows
    its own top-level package name.
    """
    derived = health.__name__.split(".")[0]
    assert derived == SHIPPING_PACKAGE_ANCHOR, (
        f"the anchor names {SHIPPING_PACKAGE_ANCHOR!r} but the shipping package this "
        f"suite imports from is {derived!r}"
    )
    assert "/" not in SHIPPING_PACKAGE_ANCHOR, (
        "the anchor carries a path separator, so it names a SUBPACKAGE and the breadth "
        "arms below would grade only part of the shipping tree"
    )


def test_the_shell_anchor_names_the_electron_package() -> None:
    """Same reasoning, derived from the marker file rather than from a literal."""
    assert "/" not in SHELL_ANCHOR, "the shell anchor names a subdirectory, not the shell"
    anchor = REPO_ROOT / SHELL_ANCHOR
    assert (anchor / "package.json").is_file(), (
        f"{SHELL_ANCHOR}/ carries no package.json, so it is not the Electron package"
    )
    assert not (anchor / "__init__.py").exists(), (
        f"{SHELL_ANCHOR}/ is a Python package, so the anchor has been pointed at the "
        "shipping package rather than at the shell"
    )


def test_the_population_covers_every_shipping_package() -> None:
    """Derived by LISTING the packages, so adding one cannot go unswept either.

    The anchor is spelled in this arm rather than read from POPULATION_ROOTS, so
    narrowing that knob cannot narrow the expectation with it. This is the arm
    that kills the survivor which dropped 28 of 49 files with nothing red.
    """
    anchor = REPO_ROOT / SHIPPING_PACKAGE_ANCHOR
    packages = sorted(
        directory
        for directory in anchor.iterdir()
        if directory.is_dir() and (directory / "__init__.py").is_file()
    )
    package_count = len(packages)
    assert package_count > 0, "no package directory was found; this arm would prove nothing"
    members = population_files()
    unswept = sorted(
        package.name
        for package in packages
        if not any(package in member.parents for member in members)
    )
    unswept_count = len(unswept)
    assert unswept_count == 0, (
        f"{unswept_count} of {package_count} shipping package(s) contribute no file to "
        f"the population: {unswept}"
    )


def test_the_population_covers_the_electron_shell() -> None:
    """``shell/`` is in scope by decision, argued in the module docstring."""
    anchor = REPO_ROOT / SHELL_ANCHOR
    assert anchor.is_dir(), "the Electron shell is not where this arm says it is"
    contributed = [member for member in population_files() if anchor in member.parents]
    contributed_count = len(contributed)
    assert contributed_count > 0, "the population reaches no file under the Electron shell"


def test_the_population_is_a_superset_of_the_anchored_corpus() -> None:
    """Pins the population root in the NARROWING direction, from anchors of its own."""
    expected = frozenset(_anchored_corpus())
    expected_count = len(expected)
    assert expected_count > 0, "the anchored corpus is empty; this arm would prove nothing"
    missing = _relative(expected - frozenset(population_files()))
    missing_count = len(missing)
    assert missing_count == 0, (
        f"{missing_count} anchored file(s) are outside the population, the first few "
        f"being {missing[:5]}"
    )


@pytest.mark.parametrize("suffix", POPULATION_SUFFIXES)
def test_the_population_holds_at_least_one_file_of_every_graded_suffix(suffix: str) -> None:
    matched_count = len([path for path in population_files() if path.suffix == suffix])
    assert matched_count > 0, f"the population matched no {suffix} file, so it grades none"


@pytest.mark.parametrize(
    "relative",
    [
        "clockspeed/surface/server.py",
        "clockspeed/surface/api/health.py",
        "clockspeed/surface/api/pending.py",
        "clockspeed/surface/api/routes.py",
        "clockspeed/surface/api/solve.py",
        "clockspeed/surface/web/app.js",
        "clockspeed/surface/web/index.html",
        "clockspeed/data/registry.py",
        "clockspeed/save/header.py",
        "shell/main.js",
    ],
)
def test_the_population_contains_every_known_carrier(relative: str) -> None:
    members = frozenset(_relative(population_files()))
    assert relative in members, f"the population does not reach a known carrier: {relative}"


@pytest.mark.parametrize("prefix", FORBIDDEN_POPULATION_PREFIXES)
def test_the_population_excludes_the_recording_trees(prefix: str) -> None:
    """Pins the population root in the WIDENING direction.

    Test trees and docs RECORD these sentences on purpose. Widening the root
    toward the repository root pulls them in and this arm dies.
    """
    strays = [member for member in _relative(population_files()) if member.startswith(prefix)]
    stray_count = len(strays)
    assert stray_count == 0, f"the population reached {stray_count} file(s) under {prefix}"


@pytest.mark.parametrize("part", EXCLUDED_PATH_PARTS)
def test_the_population_excludes_every_declared_path_component(part: str) -> None:
    strays = [member for member in population_files() if part in member.parts]
    stray_count = len(strays)
    assert stray_count == 0, (
        f"{stray_count} population file(s) carry the excluded path component {part}"
    )


def test_the_excluded_adr_would_redden_this_guard() -> None:
    """The control that makes the ADR exclusion a decision rather than a typo.

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
        f"{offender_count} place(s) in the shipping tree restate the size of the "
        f"published route set - {offenders} - and the owner of that number is "
        "health.ENDPOINT_TEMPLATES, not a docstring or a comment"
    )
