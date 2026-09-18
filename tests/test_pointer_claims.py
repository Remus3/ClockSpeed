"""The CS-937 claim leg: a line pointer answers to its own citing sentence.

A SIBLING OF ``tests/test_docs_citations.py`` RATHER THAN A PART OF IT, and the
split was ordered by a guard rather than chosen. The leg landed inside that
module and pushed it to 94.8 per cent of the tests-tree size ceiling, past the
approach band; ``tests/data/test_phase2_gate.py`` names the remedy in the
failure text it prints - RELOCATE a block of arms into a sibling module, do NOT
delete an arm and do NOT raise the ceiling. This file is that relocation. No
assertion was loosened in it and no arm was dropped.

WHAT STAYED BEHIND, AND WHY EXACTLY THOSE. The three compiled patterns this leg
reads by - a backticked span, a sentence boundary, a line-leading comment
marker - stay in ``tests/test_docs_citations.py``, because the arm that holds
every ``*_RE`` name in a module answerable to a registry reads that module's
own ``globals()``. Moving the patterns would move them out from under the only
walk that counts them, which is the evasion-by-relocation
:func:`tests.bare_path_guard.registry_problems` exists to refuse. They are
imported here by name.

THE TABLES AND THEIR CONTRACTS TRAVELLED TOGETHER, which is the same rule read
the other way: a bounded table must name a contract the module that HOLDS it
defines. Both tables this leg forgives through are declared below, both are
registered below, and both contracts are arms in this file.

THE FIXTURES ARE BOUND BY NAME because pytest resolves a fixture out of the
COLLECTING module's namespace, so one defined a file over is invisible until
its name is bound here - the idiom ``tests/test_docs_citations.py`` records at
length and this file follows without restating the reasoning.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Final

from tests import test_citation_tables as tables
from tests.test_citation_tables import (
    NEWLINE,
    Disposition,
    line_key,
)
from tests.test_citation_tables import (
    file_lines as _file_lines,
)
from tests.test_citation_tables import (
    line_pointer_carriers as _line_pointer_carriers,
)
from tests.test_citation_tables import (
    tracked as _tracked,
)
from tests.test_docs_citations import (
    BACKTICK_RE,
    LINE_MARKER_RE,
    SENTENCE_BREAK_RE,
    landing_digest,
    line_pointer_sites,
)
from tests.test_docs_citations import (
    live_line_pointers as _live_line_pointers,
)

tracked = _tracked
file_lines = _file_lines
line_pointer_carriers = _line_pointer_carriers
live_line_pointers = _live_line_pointers


@dataclass(frozen=True)
class ClaimResidual:
    """One non-Python pointer whose citing sentence its landing does not carry.

    TWO FIELDS, AND THE SECOND IS THE POINT. The Python leg grandfathers its
    residual with a bare digest, and its own module says why that is thin: a
    bare pin "lets a KNOWN-WRONG pointer be recorded away with the same shrug
    as an unexamined one, which is laundering". A row here cannot be written
    without saying what is known about the site, and
    ``test_every_recorded_pointer_claim_states_what_is_known`` reddens on an
    empty one - so the disclosure is mechanical rather than a habit.

    Attributes:
        digest: :func:`landing_digest` of the line the record was taken
            against. A later edit that moves the landing reddens rather than
            being absorbed, for the reason
            :data:`tests.test_citation_tables.UNVERIFIED_LINE_POINTERS` gives.
        why: What is known about this site, stated by whoever recorded it.
    """

    digest: str
    why: str


#: THE CLAIM RESIDUAL. Every non-Python line pointer whose sentence spells a
#: claim the landing does not carry, with what is known about each.
#:
#: IT IS NOT A DISPOSITION AND MUST NOT BECOME ONE. A `Disposition` answers a
#: pointer - somebody read it and ruled - and spending one moves
#: :data:`tests.test_citation_tables.FORGIVEN_LINE_POINTER_CEILING`. A row
#: here answers nothing; it records that the claim does NOT hold, names what
#: is known, and pins the landing so the site cannot drift further in silence.
#: Conflating the two would let a budget built for the symbol-form leg pay for
#: a defect on a different leg.
#:
#: THE ONE ROW IS A MEASURED DEFECT, NOT AN UNEXAMINED ONE. `docs/LEDGER.md`
#: is append-only by its own header, so the pointer cannot be re-cut in place
#: and the repair route this project states - cite by name - is unavailable to
#: it. The repair is filed rather than improvised here.
#: THE DECLINE SET. Every non-Python line pointer whose citing sentence spells
#: no claim token, so this leg has nothing to grade it against. A decline is
#: NOT a pass: the site still faces legs 1 and 2, and it is pinned here so the
#: unverifiable share cannot widen without somebody deciding that it should.
POINTER_CLAIM_DECLINES: Final[frozenset[tuple[str, str, int]]] = frozenset(
    (
        ("docs/LEDGER.md", ".github/workflows/tier1.yml", 130),
        ("tests/test_docs_citations.py", ".github/workflows/tier1.yml", 250),
    )
)


UNVERIFIED_POINTER_CLAIMS: Final[Mapping[tuple[str, str, int], ClaimResidual]] = {
    ("docs/LEDGER.md", ".github/workflows/tier1.yml", 250): ClaimResidual(
        digest="dc72a3e2bbf5",
        why=(
            "MEASURED WRONG, not unexamined. The sentence claims CI runs mypy bare"
            " at this line; the workflow grew and that step is now far below it."
            " The carrier is append-only, so the pointer cannot be re-cut - the"
            " repair is CS-1144."
        ),
    ),
}


# --- CS-937: a line pointer graded against what its own sentence CLAIMS -----
#
# WHAT LEGS 1 AND 2 LEAVE OPEN, measured rather than argued. Leg 1 asks
# whether the landing carries ANYTHING; leg 2 refuses the line form outright,
# but only where a symbol form exists, so every pointer at a `.md`, `.yml` or
# `.toml` target is exempt from it by construction. A pointer at a real line
# of the WRONG rule is therefore green on both. That is not hypothetical: the
# `tools/` prohibition pointer in `tests/test_precommit_gate.py` named a line
# holding the raw-docs paragraph, stayed green for three weeks, and was WRONG
# WHEN WRITTEN rather than rotted - established against the citing commit by
# an adjudicator, not assumed.
#
# THE CLAIM IS TAKEN FROM THE CARRIER, WHICH IS WHY THIS CATCHES A POINTER
# THAT WAS NEVER RIGHT. CS-889 priced a content-anchored resolver and refused
# it because its pin would be DERIVED from today's tree, so it would freeze
# whatever each pointer currently lands in and ship green on the very defects
# it was built for. Reading the claim out of the CITING SENTENCE inverts that:
# the sentence is what a human wrote down about the target, so a pointer that
# never named its own subject disagrees with it from the first run.
#
# AND IT IS NOT A PROSE MATCHER, which is the other half of the acceptance.
# Nothing here reads meaning. A CLAIM TOKEN is a path-shaped, dotted,
# underscored or backticked-phrase span the sentence itself spells - the
# vocabulary is closed and mechanical - and the test is presence of ONE of
# them on the landing line, whitespace collapsed. So a reindent, a
# re-wrapping or a trailing-whitespace sweep of the target cannot spend an
# adjudication, and the reflow arm named in this module's CS-937 controls
# holds that direction open.
#
# THE TWO EXCLUSIONS ARE THE CS-899 FENCE, NOT TIDINESS. The target's own path
# and the carrier's own path are struck from the vocabulary. A sentence
# citing `docs/ARCHITECTURE.md` almost always spells that name, so admitting
# it would let the file name match the file name and forgive every dead
# pointer into the file at once - which is exactly the markdown keyword
# detector CS-899 priced and REFUSED for failing in the permissive direction.
#
# A SENTENCE THAT CLAIMS NOTHING IS DECLINED, NEVER PASSED. "Graded against
# what its own sentence claims" has no content when the sentence makes no
# checkable claim, so those sites are reported as DECLINED and counted, the
# way :func:`tests.test_docs_citations.line_pointer_problems` declines the
# ledger's own line numbers.
# Declining is not forgiving: a declined site still faces legs 1 and 2.

#: A claim token must be at least this wide. Four is the floor CS-936 names
#: for the same reason: a three-letter fragment matches by accident.
CLAIM_TOKEN_FLOOR: Final = 4

#: Stripped from a candidate's edges before it is judged. Markdown emphasis is
#: in the set because a bold run put `NEUTRAL.**` into the vocabulary on the
#: first live reading - an English word wearing a dot, which then reported a
#: finding against a line that was never its subject. A four-letter common
#: word cannot manufacture a finding here for the same reason CS-936 states it.
CLAIM_TOKEN_EDGES: Final = "`\"'()[],;:*"  # noqa: S105 - punctuation, not a secret

#: A token must carry a separator, so it is a path, a dotted or underscored
#: name, or a backticked phrase rather than an English word. A SLASH COUNTS
#: ANYWHERE, because a trailing one is this repository's spelling of a package
#: - `tools/`, `clockspeed/`. A DOT OR AN UNDERSCORE MUST BE INTERIOR: a
#: trailing dot is sentence punctuation, and admitting it is what let an
#: ordinary word through.
CLAIM_TOKEN_MARKS: Final = (".", "_")


def claim_sentence(text: str, pointer: str) -> str:
    """The one sentence a pointer sits in, markers stripped.

    Args:
        text: The carrier's text.
        pointer: The pointer as spelled, ``path:line``.

    Returns:
        The sentence containing the FIRST occurrence of ``pointer``, with
        line-leading comment and list markers removed and whitespace
        collapsed, or ``""`` when the pointer is not in the text.
    """
    at = text.find(pointer)
    if at < 0:
        return ""
    start = 0
    for match in SENTENCE_BREAK_RE.finditer(text[:at]):
        start = match.end()
    tail = at + len(pointer)
    ahead = SENTENCE_BREAK_RE.search(text[tail:])
    end = tail + ahead.start() if ahead is not None else len(text)
    return " ".join(LINE_MARKER_RE.sub(" ", text[start:end]).split())


def claim_tokens(sentence: str, target: str, carrier: str) -> tuple[str, ...]:
    """The spans a sentence spells that a target line can be checked against.

    Args:
        sentence: The output of :func:`claim_sentence`.
        target: The pointer's target path, struck from the vocabulary.
        carrier: The citing file's path, struck for the same reason.

    Returns:
        The claim tokens, deduplicated and ordered, possibly empty. An empty
        result means the sentence makes no checkable claim - it does NOT mean
        the pointer is good.
    """
    struck = {target.lower(), carrier.lower()}
    struck |= {path.rsplit("/", 1)[-1].lower() for path in (target, carrier)}
    candidates: list[str] = BACKTICK_RE.findall(sentence)
    candidates += BACKTICK_RE.sub(" ", sentence).split()
    tokens: list[str] = []
    for raw in candidates:
        token = raw.strip().strip(CLAIM_TOKEN_EDGES).rstrip(".")
        if len(token) < CLAIM_TOKEN_FLOOR:
            continue
        interior = token[1:-1]
        bare = "/" not in token and " " not in token
        if bare and not any(mark in interior for mark in CLAIM_TOKEN_MARKS):
            continue
        low = token.lower()
        if any(name in low or low in name for name in struck):
            continue
        if token not in tokens:
            tokens.append(token)
    return tuple(tokens)


def carried_by(tokens: Iterable[str], landing: str) -> bool:
    """Whether the landing line spells at least one of the claim tokens.

    WHITESPACE IS COLLAPSED ON BOTH SIDES, which is the whole of the reflow
    tolerance. Nothing else about the line is normalised, so a token that
    stops appearing because the line now says something else is a finding.

    Args:
        tokens: The claim tokens.
        landing: The target line, as read from the file.

    Returns:
        True when any token appears in the collapsed landing.
    """
    flat = " ".join(landing.split())
    return any(" ".join(token.split()) in flat for token in tokens)


def line_pointer_claim_problems(
    other_sites: Iterable[tuple[str, str, int, str]],
    carriers: Mapping[str, str],
    residuals: Mapping[tuple[str, str, int], ClaimResidual] | None = None,
    dispositions: Mapping[tuple[str, str], Disposition] | None = None,
) -> tuple[list[str], list[str]]:
    """Grade every non-Python pointer against its own citing sentence.

    Args:
        other_sites: The non-Python half of :func:`line_pointer_sites`. The
            Python half is not read: leg 2 refuses the line form there
            outright, so a claim check would grade a site already condemned.
        carriers: Carrier path to the text its pointers are read out of.
        residuals: The recorded sites whose claim does NOT hold, each stating
            what is known about it and pinned to the landing it was recorded
            against.
        dispositions: The adjudicated answers, keyed by :func:`line_key`. A
            site somebody read and ruled on is answered and not re-graded.

    Returns:
        ``(problems, declined)``. DECLINED is every site whose sentence spells
        no claim token, reported so the unverifiable share stays countable
        rather than looking like a pass.
    """
    table = tables.DISPOSITIONS if dispositions is None else dispositions
    recorded = dict(UNVERIFIED_POINTER_CLAIMS if residuals is None else residuals)
    problems: list[str] = []
    declined: list[str] = []
    for carrier, path, line, landing in other_sites:
        if table.get((carrier, line_key(path, line))) is not None:
            continue
        sentence = claim_sentence(carriers.get(carrier, ""), f"{path}:{line}")
        tokens = claim_tokens(sentence, path, carrier)
        if not tokens:
            declined.append(
                f"{carrier} -> {path} line {line} - its sentence spells no claim token,"
                " so there is nothing to grade the landing against"
            )
            continue
        if carried_by(tokens, landing):
            continue
        residual = recorded.get((carrier, path, line))
        if residual is None:
            problems.append(
                f"{carrier} -> {path} line {line} - its sentence claims"
                f" {list(tokens)}, and the line reads {landing.strip()!r}."
                " The pointer does not name its own subject."
            )
        elif residual.digest != landing_digest(landing):
            problems.append(
                f"{carrier} -> {path} line {line} - RECORDED, BUT THE LINE HAS MOVED"
                f" UNDER THE RECORD. It now reads {landing.strip()!r}, which is not"
                " what the record was taken against. Re-read it and restate the"
                " record, or repair the pointer - re-cutting the digest keeps a"
                " record of a landing nobody has seen."
            )
    return problems, declined


#: EVERY FORGIVENESS TABLE THIS MODULE HOLDS, and the contract that BOUNDS it.
#: THE REGISTRY TRAVELS WITH THE TABLES, which is what
#: :func:`tests.bare_path_guard.registry_problems` requires of any module in
#: this family: a table declared one file away from the arm that bounds it is a
#: table the single-module walk cannot see.
#:
#: NEITHER IS BOUNDED BY A CEILING AND THAT IS STRICTER, not looser. Both
#: contracts are EXACT SETS in both directions, so a new row and a stale row
#: each redden on their own. A ceiling is the weaker instrument and is right
#: only where the population cannot be derived; here it can.
FORGIVENESS_TABLES: Final[Mapping[str, str]] = {
    "UNVERIFIED_POINTER_CLAIMS": "test_the_recorded_pointer_claims_are_pinned_in_both_directions",
    "POINTER_CLAIM_DECLINES": "test_the_pointer_claim_declines_are_pinned_in_both_directions",
}

#: The other half of the same walk: every module-scope container here that
#: forgives NOTHING, with the reason it does not.
NOT_A_FORGIVENESS: Final[Mapping[str, str]] = {
    "CLAIM_TOKEN_MARKS": "the separators a claim token must carry; widening only adds findings",
    "_CLAIM_CORPUS": "a synthetic corpus a control judges against",
    "FORGIVENESS_TABLES": "the registry itself, walked by the contract that reads it",
    "NOT_A_FORGIVENESS": "the registry itself, walked by the contract that reads it",
}


def test_no_line_pointer_contradicts_its_own_citing_sentence(
    live_line_pointers: tuple[list[tuple[str, str, int, str]], list[tuple[str, str, int, str]]],
    line_pointer_carriers: Mapping[str, str],
) -> None:
    """LEG 3. The landing spells something the citing sentence claims of it.

    READ OVER THE NON-PYTHON HALF ONLY. Leg 2 refuses the line form at a
    tracked Python module outright, so a claim check there would grade a site
    already condemned and would report the same pointer twice.
    """
    _py_sites, other_sites = live_line_pointers

    problems, _declined = line_pointer_claim_problems(other_sites, line_pointer_carriers)

    assert not problems, (
        "line pointers that do not name their own subject:"
        + NEWLINE
        + NEWLINE.join(f"  {problem}" for problem in problems)
    )


def test_the_recorded_pointer_claims_are_pinned_in_both_directions(
    live_line_pointers: tuple[list[tuple[str, str, int, str]], list[tuple[str, str, int, str]]],
    line_pointer_carriers: Mapping[str, str],
) -> None:
    """The contract on :data:`UNVERIFIED_POINTER_CLAIMS`, an exact set.

    BOTH DIRECTIONS, so the table cannot grow in silence and cannot outlive
    its corpus. A newly contradicting pointer is not in the table and reddens;
    a repaired one is in the table with nothing to forgive and reddens too.
    An exact set is a stronger bound than a ceiling and needs no budget - the
    table's whole purpose is to shrink to nothing.
    """
    _py_sites, other_sites = live_line_pointers

    failing, _declined = line_pointer_claim_problems(other_sites, line_pointer_carriers, {})
    contradicting = {
        problem.split(" - ", 1)[0].replace(" -> ", "|").replace(" line ", "|")
        for problem in failing
    }
    recorded = {f"{carrier}|{path}|{line}" for carrier, path, line in UNVERIFIED_POINTER_CLAIMS}

    assert contradicting == recorded, (
        f"the claim residual is {len(contradicting)} site(s), recorded at {len(recorded)}."
        f"{NEWLINE}  arrived: {sorted(contradicting - recorded)}"
        f"{NEWLINE}  gone: {sorted(recorded - contradicting)}"
    )


def test_every_recorded_pointer_claim_states_what_is_known() -> None:
    """A row cannot be written without disclosing what is known about it.

    THIS IS THE ANTI-LAUNDERING PROPERTY, mechanical rather than habitual. The
    Python leg's bare-digest pin can record a KNOWN-WRONG pointer with the same
    shrug as an unexamined one, which its own module names as laundering. A
    row here carries a `why` and this arm reddens on an empty one.
    """
    problems = [
        f"{carrier} -> {path} line {line} - {fault}"
        for (carrier, path, line), residual in UNVERIFIED_POINTER_CLAIMS.items()
        for fault in (["states no reason"] if not residual.why.strip() else [])
        + (
            []
            if re.fullmatch(r"[0-9a-f]{12}", residual.digest)
            else ["its digest is not twelve hex characters"]
        )
    ]

    assert not problems, "rows recorded without disclosure:" + NEWLINE + NEWLINE.join(problems)


def test_the_pointer_claim_declines_are_pinned_in_both_directions(
    live_line_pointers: tuple[list[tuple[str, str, int, str]], list[tuple[str, str, int, str]]],
    line_pointer_carriers: Mapping[str, str],
) -> None:
    """The contract on :data:`POINTER_CLAIM_DECLINES`, an exact set.

    A DECLINE IS NOT A PASS AND IS COUNTED SO IT CANNOT LOOK LIKE ONE. A
    sentence that spells no claim token leaves this leg nothing to grade, and
    the honest report of that is a decline - but an uncounted decline is a
    hole that widens every time somebody writes a pointer into prose that says
    nothing about the target. Pinning the set makes each new one a decision.
    """
    _py_sites, other_sites = live_line_pointers

    _problems, declined = line_pointer_claim_problems(other_sites, line_pointer_carriers, {})
    live = {
        entry.split(" - ", 1)[0].replace(" -> ", "|").replace(" line ", "|") for entry in declined
    }
    pinned = {f"{carrier}|{path}|{line}" for carrier, path, line in POINTER_CLAIM_DECLINES}

    assert live == pinned, (
        f"the decline set is {len(live)} site(s), pinned at {len(pinned)}."
        f"{NEWLINE}  arrived: {sorted(live - pinned)}"
        f"{NEWLINE}  gone: {sorted(pinned - live)}"
    )


def test_a_multi_word_claim_survives_a_respaced_target() -> None:
    """The whitespace collapse in :func:`carried_by`, pinned in BOTH directions.

    ADDED ON A VERIFIER'S CORRECTION, and the correction is worth recording
    because it is the shape an arm most often hides. The reflow arm above
    stays green across a respaced target - but both of its claim tokens are
    single words, so the collapse never decides anything there and the arm was
    green under a matcher that did not collapse at all. A multi-word claim is
    the only shape that reaches the branch, so it gets its own arm.

    THE SECOND ASSERT IS WHAT STOPS THE COLLAPSE BECOMING A PROSE MATCHER. A
    line that has been re-spaced still carries the claim; a line that says
    something else does not, however it is spaced.
    """
    claim = ("never imported by",)

    assert carried_by(claim, "-  `tools/`  is   never    imported   by  `clockspeed/`."), (
        "a respaced target dropped a multi-word claim, so the collapse is not reached"
    )
    assert not carried_by(claim, "- `tools/` is never exported by `clockspeed/`."), (
        "a line that says something else matched, so the collapse forgives content"
    )


def test_a_claim_token_is_never_an_ordinary_word_wearing_punctuation() -> None:
    """The control on the vocabulary, planted from the live reading that failed.

    A bold run in `docs/LEDGER.md` put `NEUTRAL.**` into the vocabulary on the
    first live reading of this leg and manufactured a finding against a line
    that was never its subject. The fixture is that exact shape.
    """
    sentence = "**THE HEADER EDIT IS LINE-COUNT NEUTRAL.** See docs/synthetic/seams.md:3."

    tokens = claim_tokens(sentence, "docs/synthetic/seams.md", "docs/synthetic/carrier.md")

    assert not tokens, f"an ordinary word was admitted as a claim token: {list(tokens)}"


def test_a_directory_token_survives_its_trailing_slash() -> None:
    """The other direction of the same rule, so the fix cannot over-narrow.

    A trailing dot is sentence punctuation and is struck. A trailing SLASH is
    this repository's spelling of a package and must survive, or the one live
    site that verifies today stops verifying and the leg goes vacuous.
    """
    sentence = "It prohibits clockspeed/ importing tools/."

    tokens = claim_tokens(sentence, "docs/synthetic/seams.md", "docs/synthetic/carrier.md")

    assert set(tokens) == {"clockspeed/", "tools/"}, f"got {sorted(tokens)}"


# --- the CS-937 controls: a pointer graded against its own sentence ---------
#
# THE TWO ARMS ITS ACCEPTANCE NAMES, and they pull in opposite directions on
# purpose. One reddens when the pointer is silently moved onto a different
# non-blank line - the defect leg 1 cannot see, because the new landing is not
# blank. The other stays GREEN when the landing is reflowed and says the same
# thing, which is what stops the grader from being a prose matcher that spends
# an adjudication on a whitespace sweep.

_CLAIM_TARGET: Final = "docs/synthetic/seams.md"
_CLAIM_CARRIER: Final = "docs/synthetic/carrier.md"

_CLAIM_CORPUS: Final = {
    _CLAIM_TARGET: [
        "# Seam discipline",
        "",
        "- `tools/` is never imported by `clockspeed/`. Gates depend on the product.",
        "- `solve/` never reads a save. It takes a registry and a request.",
    ],
}


def _claim_carrier(line: int) -> dict[str, str]:
    """One carrier whose sentence claims what the pointed-at line says."""
    return {
        _CLAIM_CARRIER: (
            f"The seam is not violated: {_CLAIM_TARGET}:{line} prohibits clockspeed/"
            " importing tools/ and NOT the reverse."
        )
    }


def test_a_pointer_retargeted_to_a_different_non_blank_line_is_reported() -> None:
    """ARM ONE. The landing is real, so leg 1 is silent - this arm is not."""
    lines = dict(_CLAIM_CORPUS)
    _py, other = line_pointer_sites(_claim_carrier(4), lines)
    assert other, "the fixture produced no judgeable site, so the arm proves nothing"

    problems, _declined = line_pointer_claim_problems(other, _claim_carrier(4), {})

    assert problems, (
        "a pointer moved from the `tools/` clause onto the `solve/` clause was"
        " accepted; the sentence's claim was never read"
    )


def test_a_whitespace_only_reflow_of_the_target_stays_green() -> None:
    """ARM TWO. The claim still holds, so nothing is spent on a reindent."""
    reflowed = {
        _CLAIM_TARGET: [
            "# Seam discipline",
            "",
            "-   `tools/`  is  never   imported  by  `clockspeed/`. Gates depend on the product.",
            "- `solve/` never reads a save. It takes a registry and a request.",
        ]
    }
    _py, other = line_pointer_sites(_claim_carrier(3), reflowed)
    assert other, "the fixture produced no judgeable site, so the arm proves nothing"

    problems, _declined = line_pointer_claim_problems(other, _claim_carrier(3), {})

    assert not problems, (
        "a whitespace-only reflow of the target reddened the grader, which is the"
        " prose-matcher failure the acceptance forbids:" + NEWLINE + NEWLINE.join(problems)
    )
