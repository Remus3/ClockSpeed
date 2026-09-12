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

THE CORPUS IS GRADED BY SET EQUALITY, AND THAT REPLACED THREE ROUNDS OF PINS.
The worst survivor of round one moved the population root from ``clockspeed`` to
``clockspeed/surface`` and dropped 28 of 49 files - every module under ``data/``,
``save/``, ``solve/``, ``audit/``, ``progress/`` and ``advisor/`` - with nothing
red. Round two pinned the root with an ANCHOR; round three's adversary narrowed
the anchor's own helper, and then narrowed the anchor AT ITS USE SITE by
concatenating ``"/surface"`` onto it, rebuilding the original defect without
touching a single literal and leaving 9 of 10 ``shell/`` files unswept with 452
arms green. The unpinned knob had simply moved up a level each time, because
every pin is itself a value for the next pass to find.

So the construction changed instead. :func:`population_files` is enumerated at
run time, :func:`independently_walked_corpus` derives the same corpus a second
time by ``os.walk`` with its own roots, suffixes and exclusions spelled as
literals that appear nowhere else in this module, and
:func:`test_the_swept_corpus_equals_an_independently_walked_corpus` asserts the
two sets are EQUAL - not a superset, and not one-file-per-package, both of which
a shrink can satisfy. No config change at any level can shrink the corpus without
that arm dying, because the two derivations would have to be wrong the SAME way.
:func:`test_the_independent_walk_is_not_vacuous` puts the floor on the WALK
rather than on the sweep, so an empty-set equality cannot pass either. The
honest residual, stated rather than left to be found: a mutation that edits BOTH
spellings identically survives, and no single-edit mutation does.

ONE MUTANT SURVIVES THE EQUALITY ARM AND IS EQUIVALENT RATHER THAN LIVE, which
is a different thing and is measured, not asserted. Adding ``docs`` to
:data:`POPULATION_ROOTS` leaves every arm green because ``docs/`` holds ZERO of
its 36 files with a graded suffix - the same is true of ``memory/`` (0 of 21) and
``config/`` (0 of 1) - so the corpus is byte-identical either way and no value
could distinguish the two trees. The moment somebody adds a ``.py`` under
``docs/``, the mutation stops being equivalent and the equality arm reddens,
because the independent walk does not read that root. An equivalent mutant is
not a surviving one, and the way to tell them apart is to name the structural
fact that makes it equivalent.

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
RECORD the history of these sentences on purpose.

EACH EXCLUSION IS MADE BY A NAMED MECHANISM, and the mechanisms are not
interchangeable. ``tests/`` and ``shell/test/`` go out through
:data:`EXCLUDED_PATH_PARTS`, which prunes by path component. ``docs/`` and
``memory/`` go out because ``.md`` is not a graded suffix, so they hold nothing
this guard could read in the first place. ``tools/``, ``ops/`` and ``scripts/``
hold real ``.py`` files and go out only because they are not roots, which is why
those three - and ONLY those three - are named in
:data:`FORBIDDEN_POPULATION_PREFIXES`: an earlier revision listed ``docs/``,
``memory/`` and ``tests/`` there too and promised that widening the root "pulls
them in and this arm dies", which was false for all three. The inert members were
deleted and :func:`test_every_forbidden_prefix_is_live_rather_than_decorative`
now stops one being added back.

A RELATED DEAD CLAIM, corrected rather than left standing. Running this detector
over ``docs/`` fires on ``docs/ARCHITECTURE.md``'s "The five endpoints that would
surface it" - a legal subset count that only looks like an aggregate because an
authority reference happens to sit six tokens back. That is a true observation
about the heuristic and NOT a risk this population can run: ``.md`` is not a
graded suffix, so no setting of the root knob can reach it. It is recorded here
as information about the limit, and never as a site to edit.

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
  - A COMPOUND JOINED BY NEITHER A HYPHEN NOR AN UNDERSCORE - ``route/templates``
    or ``routeTemplates``. Both separators in :data:`COMPOUND_SEPARATORS` are
    split and caught. THE UNDERSCORE USED TO BE LISTED HERE as a limit, on the
    stated grounds that splitting it would make ``ENDPOINT_TEMPLATES`` yield
    "templates" and redden the sentences that correctly NAME the owner. That was
    measured and is FALSE - splitting the underscore adds zero population hits -
    so the shape was closed and the claim deleted. The remaining two are not
    closed for a stated reason: a slash would split ``/api/health`` into tokens
    and shift every distance in this repository's most common phrase, and camel
    case has no live carrier to justify a case-boundary tokenizer.
  - A COUNT SPELLED IN A WAY :data:`COUNT_WORDS` does not hold. "a dozen" and
    "twenty-one" are caught; "a handful" and "a couple" are not counts.

THE SENTENCE-BOUNDARY CASE IS A DELIBERATE DECISION, NOT AN OVERSIGHT. This
detector is a pure PROXIMITY heuristic and does not respect sentence boundaries
at all, so "``BOOTSTRAP.md`` section 7.1 is the owner. There are eleven
endpoints." IS caught, and an arm plants it. That choice is taken knowingly: this
repository's prose routinely puts the authority in one sentence and the claim in
the next, so a boundary-respecting detector would miss the house style. The cost
is a subset count sitting near an unrelated authority reference, which is the
shape ``docs/ARCHITECTURE.md`` carries and which ``pending.py`` would carry if
the span reached twelve. Inside the population that cost was measured at ZERO,
and the span is what holds it there.

WHERE AN ARM WOULD BE VACUOUS IT IS PAIRED WITH A FIRING LEG, or deleted. An
adversarial pass found three negative arms that no value of any knob could make
fire: two distributive phrases carried no authority token, so they were green for
that reason rather than because of the distributive skip, and one "legal subset"
sentence had neither a count-noun pair nor an authority token and was doubly
vacuous. The vacuous sentence was deleted; the other two were extended with an
authority reference, which departs from the live text on purpose; and every
member of :data:`LEGAL_SUBSET_SENTENCES` and :data:`DISTRIBUTIVE_PHRASES` now
carries a paired arm asserting that it DOES fire once the one feature holding it
green is removed. Three of seventeen arms silently unable to fail is the
pooled-guard shape, where a population's weakest members go unmeasured while the
acceptance clause still passes.

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
import os
from pathlib import Path
from typing import Final

import pytest

from clockspeed.surface.api import health, pending, routes, solve

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

#: Turned into whitespace before tokenizing, so ``route-templates`` reads as two
#: tokens, ``twenty-one`` as a count, and ``route_templates`` as two as well.
#: The underscore is here BY MEASUREMENT: a previous revision of this module
#: declined to split it on the stated grounds that ``ENDPOINT_TEMPLATES`` would
#: then yield the token "templates" and redden the sentences that correctly NAME
#: the owner. That cost was measured and does not exist - splitting the
#: underscore adds ZERO population hits - so the claim was deleted rather than
#: defended, and the shape is now closed.
COMPOUND_SEPARATORS: Final = ("-", "_")

#: Which file suffixes carry prose this guard grades.
POPULATION_SUFFIXES: Final = (".py", ".js", ".html")

#: Where the population is rooted: the shipping Python package and the Electron
#: shell. NOTHING about breadth is trusted to this knob, or to any other - the
#: corpus is graded by SET EQUALITY against an independent walk below.
POPULATION_ROOTS: Final = ("clockspeed", "shell")

#: Path components that take a file out of the population wherever they appear
#: BELOW the repository root. Test trees RECORD the history of these sentences on
#: purpose. Matched against the REPOSITORY-RELATIVE parts, not the absolute ones:
#: matching absolute parts made the whole population vanish for anyone whose
#: checkout sat under a directory named "test", and an empty population passes
#: the arm this module exists for.
EXCLUDED_PATH_PARTS: Final = ("__pycache__", "node_modules", "test", "tests")

#: Trees that must never contribute, asserted rather than assumed. Every member
#: is LIVE - it holds at least one graded-suffix file, pinned by its own arm - so
#: adding one to the roots really does redden
#: :func:`test_the_population_excludes_the_recording_trees`. Three members were
#: REMOVED from this tuple rather than kept: ``docs/`` and ``memory/`` hold no
#: graded-suffix file at all, and ``tests/`` is already removed by
#: :data:`EXCLUDED_PATH_PARTS`, so an arm naming them promised a net it did not
#: provide.
FORBIDDEN_POPULATION_PREFIXES: Final = (
    "tools/",
    "ops/",
    "scripts/",
)

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
    loosened = text
    for separator in COMPOUND_SEPARATORS:
        loosened = loosened.replace(separator, " ")
    original = tuple(loosened.split())
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
    if not path.is_file() or path.suffix not in POPULATION_SUFFIXES:
        return False
    relative = path.relative_to(REPO_ROOT).parts
    return not any(part in EXCLUDED_PATH_PARTS for part in relative)


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


def independently_walked_corpus() -> tuple[Path, ...]:
    """The corpus, derived a SECOND time by rules spelled nowhere else.

    THIS IS THE GUARANTEE, and it replaces three rounds of pins. Every earlier
    attempt to protect the corpus added a constant - a root, then an anchor for
    the root, then a private config inside the anchor's own helper - and each
    time the unpinned knob simply moved up one level and the next adversarial
    pass narrowed it there. An anchor could even be narrowed AT THE USE SITE by
    concatenation, rebuilding the original defect without touching its literal.
    Pinning values cannot close that class, because every pin is itself a value.

    So the corpus is enumerated twice by different means and asserted EQUAL -
    not a superset, and not one-file-per-package, both of which a shrink can
    satisfy. This walk shares NOTHING with :func:`population_files`: it uses
    ``os.walk`` rather than ``Path.rglob``, prunes as it descends rather than
    filtering afterwards, and spells its own roots, suffixes and exclusions as
    literals. Two derivations that both read the same knob are not independent,
    which is exactly why none of this module's constants appear below.

    A plain walk was chosen over ``git ls-files`` deliberately. Git cannot see an
    untracked file, so a newly added module would be absent from one side and
    present in the other, and this arm would redden for someone mid-edit rather
    than for a real shrink. Both sides therefore read the filesystem.

    Returns:
        Absolute paths, sorted.
    """
    graded_here = {".py", ".js", ".html"}
    pruned_here = {"__pycache__", "node_modules", "test", "tests"}
    found: list[Path] = []
    for top in ("clockspeed", "shell"):
        for directory, subdirectories, filenames in os.walk(REPO_ROOT / top):
            subdirectories[:] = [name for name in subdirectories if name not in pruned_here]
            here = Path(directory)
            found.extend(
                here / filename for filename in filenames if Path(filename).suffix in graded_here
            )
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
    expected = ("tools/", "ops/", "scripts/")
    missing = sorted(frozenset(expected) - frozenset(FORBIDDEN_POPULATION_PREFIXES))
    extra = sorted(frozenset(FORBIDDEN_POPULATION_PREFIXES) - frozenset(expected))
    drift_count = len(missing) + len(extra)
    assert drift_count == 0, (
        f"FORBIDDEN_POPULATION_PREFIXES drifted: {len(missing)} missing {missing}, "
        f"{len(extra)} extra {extra}"
    )


@pytest.mark.parametrize("prefix", FORBIDDEN_POPULATION_PREFIXES)
def test_every_forbidden_prefix_is_live_rather_than_decorative(prefix: str) -> None:
    """A forbidden prefix that could never be reached promises a net it has not got.

    Three earlier members were inert and measurably so: adding ``docs`` or
    ``memory`` to the roots left every arm green because neither holds a
    graded-suffix file, and ``tests`` was already removed by the path-component
    filter, so its prefix arm graded nothing either. They were deleted rather
    than explained. This arm is what stops one being added back.
    """
    tree = REPO_ROOT / prefix.rstrip("/")
    assert tree.is_dir(), f"{prefix} is not a directory in this repository"
    graded = [
        path for path in tree.rglob("*") if path.is_file() and path.suffix in POPULATION_SUFFIXES
    ]
    graded_count = len(graded)
    assert graded_count > 0, (
        f"{prefix} holds no file with a graded suffix, so forbidding it cannot ever "
        "redden and the exclusion is decorative"
    )


def test_the_derived_population_floors_are_pinned_in_both_directions() -> None:
    """The floors under the DERIVED plant populations are values too, so they are pinned.

    Lowered to zero, a parametrized arm over an empty derivation collects no cases
    and vanishes in silence, which is the one way a derived population can still
    grade nothing.
    """
    expected_subset = 3
    expected_distributive = 2
    assert expected_subset == MINIMUM_LIFTED_SUBSET_SENTENCES, (
        f"the subset floor is {MINIMUM_LIFTED_SUBSET_SENTENCES}, not {expected_subset}"
    )
    assert expected_distributive == MINIMUM_LIFTED_DISTRIBUTIVE_SENTENCES, (
        f"the distributive floor is {MINIMUM_LIFTED_DISTRIBUTIVE_SENTENCES}, not "
        f"{expected_distributive}"
    )


def test_the_authority_prefix_really_carries_an_authority() -> None:
    """Every firing leg below depends on this string carrying a token; nothing else said so."""
    _original, normalized = _tokenize(AUTHORITY_PREFIX)
    carried = sorted(frozenset(normalized) & frozenset(AUTHORITY_TOKENS))
    carried_count = len(carried)
    assert carried_count > 0, (
        "the prefix the firing legs prepend carries no authority token, so every one "
        "of them would fail for a reason unrelated to the boundary it grades"
    )


def test_the_compound_separator_membership_is_pinned_in_both_directions() -> None:
    expected = ("-", "_")
    missing = sorted(frozenset(expected) - frozenset(COMPOUND_SEPARATORS))
    extra = sorted(frozenset(COMPOUND_SEPARATORS) - frozenset(expected))
    drift_count = len(missing) + len(extra)
    assert drift_count == 0, (
        f"COMPOUND_SEPARATORS drifted: {len(missing)} missing {missing}, {len(extra)} extra {extra}"
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


def test_the_detector_fires_on_an_underscore_compound() -> None:
    """The shape a previous revision declined to close on a cost that did not exist."""
    planted = "the eleven route_templates ``BOOTSTRAP.md`` section 7.1 publishes"
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count > 0, "an underscore fused the noun to its modifier and hid the count"


def test_normalizing_keeps_letters_only_so_a_glued_section_number_still_reads() -> None:
    """Grades the ``isalpha`` in :func:`_normalize`, which nothing else did.

    ``isalnum`` would leave "section7.1" as "section71", which is not an
    authority token, and the whole sentence would go quiet. The discriminator is
    load-bearing rather than incidental, so it gets an arm of its own.
    """
    planted = "the nine endpoints, enumerated in the section7.1 listing above"
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 1, (
        "a section reference glued to its number stopped reading as an authority, so "
        "digits are no longer being dropped from a token before it is matched"
    )


def test_the_noun_search_prefers_the_noun_after_the_count() -> None:
    """Grades the ORDER of the two legs in :func:`_noun_index`, which nothing else did.

    Searching backward first pairs the count with an earlier noun, which moves
    the window's near edge left and pushes a trailing authority reference out of
    span. Forward-before-backward is the correct precedence because the noun a
    count modifies normally follows it.
    """
    planted = "the routes for nine endpoints a b c d e f g BOOTSTRAP.md names"
    hit_count = len(aggregate_count_phrases(planted))
    assert hit_count == 1, (
        "the noun search no longer prefers the noun AFTER the count, so a count is "
        "being paired with an earlier noun and its authority falls outside the span"
    )


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


#: An authority reference this module prepends to a lifted sentence to prove the
#: sentence is one token away from firing.
AUTHORITY_PREFIX: Final = "``BOOTSTRAP.md`` section 7.1 lists them."

#: Fewest live subset sentences the extraction below must find. A floor, not a
#: membership list: a list of sentences is self-deleting under parametrize, which
#: is how an earlier revision let "drop one plant" survive with 463 arms green.
MINIMUM_LIFTED_SUBSET_SENTENCES: Final = 3

#: Fewest live distributive sentences, on the same terms.
MINIMUM_LIFTED_DISTRIBUTIVE_SENTENCES: Final = 2


def _pair_slices(source: str) -> tuple[tuple[str, bool], ...]:
    """Every count-noun pair the detector's pairing step finds in SOURCE.

    The slice runs from the pair's first token through ONE TOKEN PAST the noun,
    because that trailing token is what the distributive skip reads. Taking the
    pair's own neighbourhood rather than the whole sentence is deliberate: a
    sentence lifted whole from module source can run sixty tokens, and an
    authority reference placed at its front then falls outside
    :data:`AUTHORITY_SPAN`, which made the firing legs fail for a reason that had
    nothing to do with the boundary they grade.

    Args:
        source: Module source.

    Returns:
        One entry per pair: the slice, and whether it is distributive.
    """
    original, normalized = _tokenize(source)
    found: list[tuple[str, bool]] = []
    for index, token in enumerate(original):
        if not _is_count(token, normalized[index]):
            continue
        noun_at = _noun_index(normalized, index)
        if noun_at is None:
            continue
        low = min(index, noun_at)
        high = max(index, noun_at)
        trailing = normalized[high + 1] if high + 1 < len(normalized) else ""
        found.append((" ".join(original[low : high + 2]), trailing == DISTRIBUTIVE_WORD))
    return tuple(found)


def _lifted(modules: tuple[object, ...], distributive: bool) -> tuple[str, ...]:
    """Pair slices lifted from live modules, of one kind.

    DERIVED FROM THE SHIPPING SOURCE rather than listed, which is the point. An
    earlier revision held these as literals in a parametrized tuple; dropping one
    deleted its own two arms and survived with every arm green - the same
    self-deleting-vocabulary hazard the numeric vocabularies carry a membership
    pin for. There is nothing here to drop.

    Args:
        modules: Live modules to read.
        distributive: Which kind to return.

    Returns:
        Distinct slices, longest first so the sample is stable.
    """
    found: set[str] = set()
    for module in modules:
        for slice_text, is_distributive in _pair_slices(inspect.getsource(module)):  # type: ignore[arg-type]
            if is_distributive == distributive:
                found.add(slice_text)
    return tuple(sorted(found, key=lambda text: (-len(text), text)))


def lifted_subset_sentences() -> tuple[str, ...]:
    """Live count-noun pairs that are NOT rates - a module counting its own subset."""
    return _lifted((pending, solve), distributive=False)


def lifted_distributive_sentences() -> tuple[str, ...]:
    """Live count-noun pairs that state a RATE rather than a count."""
    return _lifted((routes, pending), distributive=True)


def test_the_lifted_sentence_populations_are_not_vacuous() -> None:
    """Both derivations must actually find something, or every arm over them is empty."""
    subset_count = len(lifted_subset_sentences())
    distributive_count = len(lifted_distributive_sentences())
    assert subset_count >= MINIMUM_LIFTED_SUBSET_SENTENCES, (
        f"the subset extraction found {subset_count} live sentence(s), fewer than the "
        f"{MINIMUM_LIFTED_SUBSET_SENTENCES} this repository carries"
    )
    assert distributive_count >= MINIMUM_LIFTED_DISTRIBUTIVE_SENTENCES, (
        f"the distributive extraction found {distributive_count} live sentence(s), "
        f"fewer than the {MINIMUM_LIFTED_DISTRIBUTIVE_SENTENCES} this repository carries"
    )


@pytest.mark.parametrize("legal", lifted_subset_sentences())
def test_the_detector_leaves_a_modules_own_subset_count_alone(legal: str) -> None:
    hit_count = len(aggregate_count_phrases(legal))
    assert hit_count == 0, "the detector fired on a module counting its own subset"


@pytest.mark.parametrize("legal", lifted_subset_sentences())
def test_every_lifted_subset_sentence_fires_with_an_authority_beside_it(
    legal: str,
) -> None:
    """The firing leg that makes the arm above grade the AUTHORITY, not the shape.

    Without it, "stayed green" and "could never have gone red" are the same
    observation. An adversarial pass found three arms in this file that no value
    of any knob could make fire, one of them a sentence with neither a count-noun
    pair nor an authority token; the extraction above cannot produce that shape,
    because it selects on the pair.
    """
    hit_count = len(aggregate_count_phrases(f"{AUTHORITY_PREFIX} {legal}"))
    assert hit_count > 0, (
        "this subset sentence does not fire even with an authority reference beside "
        "it, so the arm asserting it stays green is vacuous and grades no boundary"
    )


@pytest.mark.parametrize("distributive", lifted_distributive_sentences())
def test_the_detector_does_not_read_a_distributive_phrase_as_a_count(
    distributive: str,
) -> None:
    """Each phrase is graded WITH an authority beside it, which the live text lacks.

    Two of the three literal phrases an earlier revision used carried no
    authority token, so they were green for that reason and not because of the
    distributive skip: setting :data:`DISTRIBUTIVE_WORD` to another word killed
    exactly one of the three. Prepending the authority is what makes the skip the
    only thing holding each one green.
    """
    hit_count = len(aggregate_count_phrases(f"{AUTHORITY_PREFIX} {distributive}"))
    assert hit_count == 0, "the detector read a distributive phrase as a count"


@pytest.mark.parametrize("distributive", lifted_distributive_sentences())
def test_every_lifted_distributive_phrase_fires_once_the_rate_word_is_gone(
    distributive: str,
) -> None:
    """The firing leg for the arm above."""
    substituted = " ".join(
        "in" if _normalize(word) == DISTRIBUTIVE_WORD else word for word in distributive.split()
    )
    assert substituted != distributive, (
        f"the rate word {DISTRIBUTIVE_WORD!r} does not appear as a word in this "
        "sentence, so it cannot grade the distributive skip"
    )
    hit_count = len(aggregate_count_phrases(f"{AUTHORITY_PREFIX} {substituted}"))
    assert hit_count > 0, (
        "this phrase does not fire even with the rate word removed, so the arm "
        "asserting it stays green is vacuous and grades no boundary"
    )


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
# THE CORPUS IS GRADED BY SET EQUALITY, which is the one arm that closes the
# whole knob class instead of pinning its current members. Three rounds of pins
# each displaced the unpinned knob up a level - root, then anchor, then the
# anchor helper's own private config, then the anchor narrowed at its use site by
# concatenation - because every pin is itself a value for the next pass to find.
# Equality against a derivation that shares no constant with the first one cannot
# be satisfied by a shrink at any level: both derivations would have to be wrong
# the same way, which a single edit cannot do.
# ---------------------------------------------------------------------------


def test_the_swept_corpus_equals_an_independently_walked_corpus() -> None:
    """THE guarantee. Set equality, reported as counts plus the symmetric difference."""
    swept = frozenset(population_files())
    walked = frozenset(independently_walked_corpus())
    swept_count = len(swept)
    walked_count = len(walked)
    unswept = _relative(walked - swept)
    unexpected = _relative(swept - walked)
    difference_count = len(unswept) + len(unexpected)
    assert difference_count == 0, (
        f"the two derivations of the corpus disagree on {difference_count} file(s): "
        f"the walk found {walked_count} and the sweep {swept_count}; "
        f"{len(unswept)} walked file(s) are unswept, the first few being {unswept[:5]}; "
        f"{len(unexpected)} swept file(s) are outside the walk, the first few being "
        f"{unexpected[:5]}"
    )


def test_the_independent_walk_is_not_vacuous() -> None:
    """Equality with an empty set is not a guarantee, so the WALK has its own floor.

    Every number here is derived from the walk alone - the side that shares no
    constant with the detector - so a shrink on the other side cannot satisfy it.
    """
    walked = independently_walked_corpus()
    walked_count = len(walked)
    assert walked_count > 0, "the independent walk found nothing; equality would prove nothing"
    top_levels = {path.relative_to(REPO_ROOT).parts[0] for path in walked}
    top_level_count = len(top_levels)
    assert top_level_count > 1, (
        f"the independent walk reaches only {top_level_count} top-level tree(s) "
        f"{sorted(top_levels)}, so it cannot notice one of them being dropped"
    )
    suffixes = {path.suffix for path in walked}
    suffix_count = len(suffixes)
    assert suffix_count > 1, (
        f"the independent walk reaches only {suffix_count} suffix(es) {sorted(suffixes)}, "
        "so it cannot notice a language being dropped"
    )
    nested_depth = 2
    packages = {
        path.relative_to(REPO_ROOT).parts[1]
        for path in walked
        if path.relative_to(REPO_ROOT).parts[0] == "clockspeed"
        and len(path.relative_to(REPO_ROOT).parts) > nested_depth
    }
    package_count = len(packages)
    minimum_packages = 5
    assert package_count >= minimum_packages, (
        f"the independent walk reaches {package_count} subpackage(s) of the shipping "
        f"tree, fewer than the {minimum_packages} this repository has carried since "
        f"phase 4: {sorted(packages)}"
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
        "clockspeed/solve/ratio.py",
        "clockspeed/audit/placement.py",
        "clockspeed/progress/__init__.py",
        "clockspeed/advisor/__init__.py",
        "shell/main.js",
        "shell/preload.js",
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
