"""The worker prompt `tools/headless-queue.md` still says the things it must say.

WHAT THIS GUARDS AND WHY A GUARD IS NEEDED AT ALL. That file is not code and
nothing imports it. It is read once per cycle by a detached `claude -p` worker
with no operator present, so every property in it degrades silently: a reword
that drops a clause costs nothing at edit time and costs a whole night of
unattended cycles at run time. Prose with no test over it is prose that will
drift, and this file is the test.

WHAT IT ASSERTS ON, AND WHAT IT DELIBERATELY DOES NOT. It pins the LOAD-BEARING
TOKENS of each property - a count, a path, a name, a rule's subject - and never
a whole sentence. A guard that pins prose verbatim reddens on every honest
reword, and a guard that reddens on honest work is one somebody deletes. So the
bounded-refutation arm requires the COUNT and the word `verifier`, not the
paragraph that carries them, and it would survive that paragraph being rewritten
from scratch as long as the count survives with it.

EVERY LIVE ARM IS PAIRED WITH A NEGATIVE CONTROL, because an arm that only ever
reads a file that already satisfies it proves nothing about the arm
(CONVENTIONS.md section 7.2 - the unrun gate). Each property's predicate is a
module-level function taking the text, so a control can hand it a synthetic
document that omits exactly one token and watch the predicate report it. Without
that pairing, deleting the body of any arm below leaves this module green.

NO ARM SPAWNS A PROCESS, SLEEPS OR SHELLS OUT. The one place this module learns
anything from git is the session-scoped `repo_files` fixture in
`tests/conftest.py`, which the rest of the suite already builds once; this module
adds no subprocess of its own. That fixture is git's answer when git can answer
and a tree walk when it cannot, so the inventory arm below proves the file is
COLLECTED BY THE SUITE'S OWN INVENTORY - which is the property that matters here,
since a file the inventory misses is a file every repo-wide sweep silently skips.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parents[1]

#: The prompt under guard. Spelled ONCE: the launcher points a lane at this same
#: path, and two spellings of one path are two places for it to rot.
PROMPT_PATH: Final = "tools/headless-queue.md"

#: The sentinel a drained queue writes so the driver stops firing no-op workers.
#: Pinned as a whole path rather than as a bare name, because the NAME alone is
#: satisfied by a file written anywhere and the driver reads exactly one place.
DRAINED_SENTINEL: Final = "ops/loop/control/lanes/QUEUE_DRAINED"

#: The highest byte 7-bit ASCII admits. Bound rather than spelled at the point
#: of comparison so the number carries its meaning to the reader of the failure.
ASCII_MAX: Final = 0x7F


def prompt_bytes() -> bytes:
    """The prompt's raw bytes.

    RAW BYTES, NOT `read_text`. `Path.read_text` decodes, and on this platform
    the write side rewrites LF as CRLF while the read side hides it again - so a
    line-ending or encoding claim taken through `read_text` is a claim about the
    decoder, not about the file (CONVENTIONS.md section 10).

    Returns:
        The file's contents, undecoded.
    """
    return (REPO_ROOT / PROMPT_PATH).read_bytes()


#: The three byte faults non-negotiable 4 and CONVENTIONS.md section 10 forbid,
#: named so a failure says WHICH one fired. They are kept apart rather than
#: pooled into "the file is clean" because the repair differs for each: a BOM is
#: stripped, a high byte is retyped as ASCII, a CR is a line-ending conversion
#: to undo.
BOM = "a UTF-8 byte-order mark"
HIGH_BYTE = "a byte above 7-bit ASCII"
CARRIAGE_RETURN = "a CR byte"


def byte_faults(raw: bytes) -> list[str]:
    """Which forbidden byte faults a file carries.

    A NAMED PREDICATE RATHER THAN THREE ASSERTIONS INLINE, and the reason is
    measured rather than stylistic. Inline, the high-byte check reads a file
    that is ALREADY CLEAN, so it passes whether it grades or not: mutating its
    bound from ``> ASCII_MAX`` to ``> 0xFF`` - which no byte can exceed - left
    this module green on every arm. An assertion over a corpus with no
    violations in it is not evidence about the assertion. Pulled out here, the
    same predicate can be handed a deliberately dirty input by a control, and
    that mutant dies.

    Args:
        raw: A file's undecoded contents.

    Returns:
        The faults present, in a stable order. Empty for a clean file.
    """
    faults: list[str] = []
    if raw.startswith(b"\xef\xbb\xbf"):
        faults.append(BOM)
    if any(byte > ASCII_MAX for byte in raw):
        faults.append(HIGH_BYTE)
    if b"\r" in raw:
        faults.append(CARRIAGE_RETURN)
    return faults


def missing(text: str, required: tuple[tuple[str, str], ...]) -> list[str]:
    """Which required properties the text does not carry.

    Args:
        text: The document under test.
        required: `(label, pattern)` pairs. The pattern is a case-insensitive
            regular expression; the label is what a failure message names, so a
            reader sees the missing PROPERTY rather than a regex.

    Returns:
        The labels whose pattern found nothing, in the order given.
    """
    return [label for label, pattern in required if re.search(pattern, text, re.IGNORECASE) is None]


def present(text: str, forbidden: tuple[tuple[str, str], ...]) -> list[str]:
    """Which forbidden spellings the text DOES carry - the mirror of `missing`.

    Args:
        text: The document under test.
        forbidden: `(label, pattern)` pairs, case-insensitive.

    Returns:
        The labels whose pattern matched, in the order given.
    """
    return [label for label, pattern in forbidden if re.search(pattern, text, re.IGNORECASE)]


# --- The properties, one tuple per rule ------------------------------------
#
# Each entry is (label, pattern). The label is prose for the failure message.
# The pattern is the load-bearing token and nothing more.

#: FIX 3, and the reason this file exists. The measured failure was 7 to 10
#: refutation passes on one item with the main task still unfinished, so the
#: COUNT is the property: an unbounded "refute when uncertain" never terminates
#: because uncertainty never runs out. The three tokens are the count, the thing
#: the pass is graded AGAINST, and what happens on the second refusal.
BOUNDED_REFUTATION: Final = (
    ("the one-pass count", r"\b(one|1)\s+verifier\s+pass\b"),
    ("what the pass is graded against", r"\bstated\s+acceptance\b"),
    ("the second refusal becomes a filed row", r"\bsecond\b[\s\S]{0,400}?\bFILED\b"),
)

#: The named do-not-redo set. The two settled rules that matter most are named
#: individually rather than counted, because a count is satisfied by any two.
DO_NOT_REDO: Final = (
    ("the set is named", r"do[\s-]?not[\s-]?redo"),
    ("the zero-language-model rule", r"\b(zero|no)\s+language\s+model\b"),
    ("the never-write rule", r"never\s+writes?\s+to\s+the\s+game\s+install"),
    ("the gated fence", r"docs/GATED\.md"),
    ("the frozen-file fence", r"\bfrozen\b"),
)

#: FIX 1. The worker never blocks on CI; the driver owns every long wait and
#: writes the verdict into the cycle's own row. Both halves are pinned: the
#: DIVISION, and WHICH driver - a rule that does not name the owner is advice.
DRIVER_OWNS_THE_WAIT: Final = (
    ("the division of labour", r"driver\s+owns\s+(every|the)\s+"),
    ("which driver", r"ops/loop/queue_loop\.py"),
    ("the worker never blocks on CI", r"never\s+blocks?\s+on\s+CI"),
)

#: FIX 2's worker-side half. A crashed xdist run leaves no summary line and
#: `grep -c FAILED` over it returns 0, which reads exactly like green. BOTH
#: halves are the property, so both are pinned.
TRUNCATED_LOG_IS_NOT_GREEN: Final = (
    ("the summary line", r"summary\s+line"),
    ("the exit code", r"exit\s+code"),
)

#: The push gate. `.githooks/pre-push` runs the WHOLE suite, it is frozen, and
#: it is therefore neither the worker's to change nor its to bypass.
PUSH_GATE: Final = (
    ("the hook that gates a push", r"\.githooks/pre-push"),
    ("the bypass is forbidden", r"--no-verify"),
    ("the fast subset the worker iterates with", r"not\s+slow"),
)

#: The lane's defining constraint. A worker that loops internally accumulates
#: context until quality degrades, and a crash loses every row after the first.
ONE_ROW_PER_CYCLE: Final = (("one row, then exit", r"\bone\s+row\b"),)

#: The drained sentinel, as a whole path.
DRAINED: Final = (("the sentinel path", re.escape(DRAINED_SENTINEL)),)

#: CS-1104. A lane cycle SURFACES the cross-repo channel and never answers it.
#: The driver computes the proof; these tokens pin what the worker is TOLD. The
#: pure-read command is pinned by module, because the watcher's own entry point
#: writes its data files and its acknowledging mode marks items seen. The scope
#: sentence is two tokens, not one span, so each clause fails by name.
SURFACE_NEVER_REPLY: Final = (
    ("the channel is named", r"moon_sync_inbox"),
    ("the driver surfaces it, not the worker", r"driver\s+surfaces"),
    ("surfacing never acknowledges", r"surfacing\s+never\s+acknowledges"),
    ("composing a note is excluded", r"\bcompos(e|ing)\b[^.]{0,80}\bdeliver"),
    ("out of scope for a lane cycle", r"out\s+of\s+scope\s+for\s+a\s+lane\s+cycle"),
)

#: EVERY RULE, NAMED ONCE. Both parametrized arms read this rather than each
#: spelling its own list: a rule present in one decorator and absent from the
#: other would be a live arm with no control, or a control grading nothing, and
#: neither reports itself. One binding is one place for that to be wrong.
RULES: Final = (
    ("bounded refutation", BOUNDED_REFUTATION),
    ("the do-not-redo set", DO_NOT_REDO),
    ("the driver owns every wait", DRIVER_OWNS_THE_WAIT),
    ("a truncated log is not a green one", TRUNCATED_LOG_IS_NOT_GREEN),
    ("the push gate is neither changed nor bypassed", PUSH_GATE),
    ("one row per cycle", ONE_ROW_PER_CYCLE),
    ("the drained sentinel", DRAINED),
    ("the channel is surfaced, never answered", SURFACE_NEVER_REPLY),
)

#: THE LABEL SET OF EVERY RULE, PINNED IN BOTH DIRECTIONS. Without this the
#: cheapest way past a red arm above is to DELETE the token it failed on: the
#: live arm then passes with less to check, and both controls pass with it,
#: because each derives its expectation from the same shrunken tuple. A guard
#: that can be narrowed to fit the artifact is not grading the artifact.
#:
#: PINNED AS LABELS RATHER THAN AS A COUNT, for two reasons. A count is
#: satisfied by any replacement, so swapping a load-bearing token for a trivial
#: one would pass it. And CLAUDE.md section 4 forbids restating a measured
#: number in prose, which a literal integer here would be.
#:
#: BOTH DIRECTIONS ARE THE POINT. Adding a requirement has to be deliberate too,
#: so an append disagrees with this table and reddens - the same shape the
#: repository's other two-way pins use.
RULE_LABELS: Final = {
    "bounded refutation": frozenset(
        {
            "the one-pass count",
            "what the pass is graded against",
            "the second refusal becomes a filed row",
        }
    ),
    "the do-not-redo set": frozenset(
        {
            "the set is named",
            "the zero-language-model rule",
            "the never-write rule",
            "the gated fence",
            "the frozen-file fence",
        }
    ),
    "the driver owns every wait": frozenset(
        {"the division of labour", "which driver", "the worker never blocks on CI"}
    ),
    "a truncated log is not a green one": frozenset({"the summary line", "the exit code"}),
    "the push gate is neither changed nor bypassed": frozenset(
        {
            "the hook that gates a push",
            "the bypass is forbidden",
            "the fast subset the worker iterates with",
        }
    ),
    "one row per cycle": frozenset({"one row, then exit"}),
    "the drained sentinel": frozenset({"the sentinel path"}),
    "the channel is surfaced, never answered": frozenset(
        {
            "the channel is named",
            "the driver surfaces it, not the worker",
            "surfacing never acknowledges",
            "composing a note is excluded",
            "out of scope for a lane cycle",
        }
    ),
}

#: CS-1104, THE OTHER HALF: spellings the prompt must NEVER carry. A prompt that
#: names the sender, the acknowledging flag or the writing watcher is one reword
#: away from instructing a lane to use them. Pinned by label in both directions,
#: for the reason RULE_LABELS gives.
FORBIDDEN: Final = (
    ("the acknowledging flag", r"--ack\b"),
    ("the outbound sender", r"outbound_send"),
    ("the outbound gate", r"outbound_gate"),
    ("the watcher whose entry point writes", r"inbox_watch"),
    ("the surface, which is the driver's to run", r"inbox_surface"),
    ("a banner line that feeds sibling names to the model", r"(?m)^\s*inbox:"),
)

FORBIDDEN_LABELS: Final = frozenset(
    {
        "the acknowledging flag",
        "the outbound sender",
        "the outbound gate",
        "the watcher whose entry point writes",
        "the surface, which is the driver's to run",
        "a banner line that feeds sibling names to the model",
    }
)

#: One case per TOKEN, derived from :data:`RULES` rather than sampled. A sampled
#: hand-list leaves the tokens it omits ungraded, and the omitted one is the one
#: that rots - so the excision arm below runs over all of them.
TOKENS: Final = tuple(
    (rule, required, label) for rule, required in RULES for label, _pattern in required
)


@pytest.fixture(scope="module")
def prompt_text() -> str:
    """The prompt decoded as ASCII.

    Decoded STRICTLY: a byte outside 7-bit ASCII raises here rather than
    arriving as a replacement character that every regex below would ignore.

    Returns:
        The prompt's text.
    """
    return prompt_bytes().decode("ascii")


def test_the_worker_prompt_is_in_the_repository_inventory(
    repo_root: Path, repo_files: list[Path]
) -> None:
    """The prompt exists at the path the launcher points a lane at, and is collected.

    TWO CLAIMS, NOT ONE, and the second is the one worth testing. Existence is
    checked because a lane whose command file is absent spawns a worker with an
    empty prompt. COLLECTION is checked because `repo_files` is what every
    repo-wide sweep in this suite runs over - the 7-bit ASCII sweep in
    `tests/test_scaffold.py` among them - and a file that inventory misses is
    green everywhere while being read by nothing.

    Args:
        repo_root: Repository root.
        repo_files: The tracked-or-would-be-tracked inventory.
    """
    target = repo_root / PROMPT_PATH
    assert target.is_file(), f"{PROMPT_PATH} is missing; a lane pointed at it gets no prompt"

    collected = {path.relative_to(repo_root).as_posix() for path in repo_files}
    assert PROMPT_PATH in collected, (
        f"{PROMPT_PATH} exists but the repository inventory did not collect it, so every "
        f"repo-wide sweep skips it silently. Run `git add -N {PROMPT_PATH}`."
    )


def test_the_worker_prompt_is_seven_bit_ascii_with_lf_endings_and_no_bom() -> None:
    """The bytes obey non-negotiable 4, asserted on the bytes.

    NON-NEGOTIABLE 4 HAS A MECHANISM BEHIND IT, not a preference: Windows
    PowerShell 5.1 ANSI-decodes a BOM-less script and a UTF-8 em-dash inside a
    double-quoted string becomes a character the tokenizer reads as a string
    terminator. This prompt is piped into a worker by a PowerShell runner, so it
    travels the same path.

    THE CR CHECK IS ON DISK RATHER THAN THROUGH GIT, deliberately. The harness
    Edit tool has been measured converting tracked files to CRLF, and git
    normalises the blob and reports the tree clean while the working file
    violates the rule - so `git status` is the wrong witness here.

    The three faults are reported separately rather than pooled, because "the
    file is clean" is three different repairs depending on which one fired.
    """
    faults = byte_faults(prompt_bytes())

    assert faults == [], f"{PROMPT_PATH} carries {faults}"


@pytest.mark.parametrize(
    ("fault", "dirty"),
    [
        (BOM, b"\xef\xbb\xbfhello\n"),
        (HIGH_BYTE, b"an em-dash \xe2\x80\x94 here\n"),
        (CARRIAGE_RETURN, b"hello\r\n"),
        (BOM, b"\xef\xbb\xbf\xe2\x80\x94\r\n"),
        (HIGH_BYTE, b"\xef\xbb\xbf\xe2\x80\x94\r\n"),
        (CARRIAGE_RETURN, b"\xef\xbb\xbf\xe2\x80\x94\r\n"),
    ],
)
def test_a_dirty_file_is_reported_for_the_fault_it_carries(fault: str, dirty: bytes) -> None:
    """The negative control for the arm above, and it was NOT optional.

    THE ARM ABOVE READS A FILE THAT IS ALREADY CLEAN, so it passes whether it
    grades anything or not. MEASURED: mutating the high-byte bound from
    `> ASCII_MAX` to `> 0xFF` - which no byte can exceed, so the check can never
    fire - left every arm in this module green. That mutant SURVIVED until this
    control existed, and it is the reason `byte_faults` is a predicate rather
    than three assertions inline.

    THE FOURTH THROUGH SIXTH CASES ARE ONE INPUT CARRYING ALL THREE FAULTS,
    because a predicate that returns early after the first would answer the
    single-fault cases correctly and hide the other two.

    Args:
        fault: The fault the input carries.
        dirty: Bytes carrying it.
    """
    assert fault in byte_faults(dirty), (
        f"byte_faults did not report {fault!r} in {dirty!r}, so the live arm's green "
        f"says nothing about that fault"
    )


def test_a_clean_file_is_reported_for_nothing() -> None:
    """The other half of the control: the predicate does not fire on clean bytes.

    Paired with the arm above (CONVENTIONS.md section 7.2). A predicate hardcoded
    to report all three faults would satisfy every case above and redden the
    whole repository, so both directions are asserted.
    """
    assert byte_faults(b"plain ascii, LF only - the house rule.\n") == []


@pytest.mark.parametrize(("rule", "required"), RULES)
def test_the_worker_prompt_still_states_each_governing_rule(
    prompt_text: str, rule: str, required: tuple[tuple[str, str], ...]
) -> None:
    """Every rule the worker cannot be trusted to reinvent is still written down.

    PARAMETRIZED SO EACH RULE FAILS BY NAME. A single arm asserting a list of
    tokens reports the first miss and hides the rest, and the repair for a
    missing count is not the repair for a missing path.

    Args:
        prompt_text: The prompt.
        rule: The rule's name, for the failure message.
        required: Its `(label, pattern)` pairs.
    """
    absent = missing(prompt_text, required)

    assert absent == [], f"{PROMPT_PATH} no longer states {rule}: missing {absent}"


@pytest.mark.parametrize(("rule", "required"), RULES)
def test_a_document_stating_none_of_a_rule_is_reported_for_all_of_it(
    rule: str, required: tuple[tuple[str, str], ...]
) -> None:
    """The negative control for the arm above: the predicate can actually fail.

    THE ARM ABOVE READS A FILE THAT ALREADY SATISFIES IT, so on its own it is
    green whether it grades anything or not - gut `missing` to `return []` and
    every parametrization still passes. This hands the same predicate a document
    carrying none of the tokens and requires it to report EVERY label, which a
    gutted predicate cannot do.

    Args:
        rule: The rule's name, for the failure message.
        required: Its `(label, pattern)` pairs.
    """
    empty = "a document about something else entirely.\n"

    absent = missing(empty, required)

    assert absent == [label for label, _pattern in required], (
        f"the predicate for {rule} did not report a document that states none of it"
    )


@pytest.mark.parametrize(("rule", "required", "dropped"), TOKENS)
def test_excising_any_one_token_from_the_live_prompt_is_reported(
    prompt_text: str, rule: str, required: tuple[tuple[str, str], ...], dropped: str
) -> None:
    """EVERY token, excised from the REAL text one at a time, comes back reported.

    STRONGER THAN THE EMPTY-DOCUMENT CONTROL AND FOR A DIFFERENT REASON. An
    empty document proves the predicate reports SOMETHING. It does not prove
    that any PARTICULAR pattern is read, and a pattern that silently matches
    nothing it was meant to match would pass it. This removes one pattern's
    matches from the live prompt and requires that label back, for every token
    of every rule rather than for a chosen sample - a sample is a hand-list, and
    the token it omits is the one that rots.

    WHY THIS ASSERTS MEMBERSHIP AND NOT EQUALITY, stated rather than left as a
    weaker assertion nobody notices. One pattern in
    :data:`BOUNDED_REFUTATION` matches a SPAN - a first token, then text, then a
    second - so excising it necessarily takes its interior with it, and a
    sibling token living inside that interior goes too. Demanding `== [dropped]`
    would therefore be a claim about where the prose happens to sit rather than
    about the guard. WHAT THAT COSTS: this arm no longer detects a pattern that
    ALSO matches unrelated prose elsewhere in the file. It would not have
    detected it anyway - `re.sub` removes every match, intended and incidental
    alike, so the label goes absent under either spelling.

    Args:
        prompt_text: The prompt.
        rule: The rule's name, for the failure message.
        required: The rule's `(label, pattern)` pairs.
        dropped: The label whose pattern is excised.
    """
    gutted = re.sub(dict(required)[dropped], "", prompt_text, flags=re.IGNORECASE)

    absent = missing(gutted, required)

    assert dropped in absent, (
        f"excising {dropped!r} from the prompt left {rule} reporting {absent}, so that "
        f"pattern is not what the live arm reads"
    )


def test_no_rule_can_be_narrowed_by_deleting_one_of_its_tokens() -> None:
    """The rule tables match their pin, in both directions.

    THIS CLOSES THE CHEAPEST WAY PAST EVERY ARM ABOVE. When a reword reddens the
    live arm, the one-line repair that makes it green is to delete the token it
    failed on - and nothing above notices, because the live arm then has less to
    check and BOTH controls derive their expectation from the same shrunken
    tuple. A guard that can be narrowed to fit the artifact is not grading it.

    IT FAILS ON AN ADDITION TOO, deliberately. Adding a requirement should be as
    deliberate as removing one, and a pin that only catches deletion teaches
    that appending is free.
    """
    live = {rule: frozenset(label for label, _pattern in required) for rule, required in RULES}

    assert live == dict(RULE_LABELS), (
        "the rule tables and their pin disagree. If a token was deleted, restore it - "
        "reword the PROMPT to satisfy it, never the guard to excuse it. If one was added "
        "on purpose, add it to RULE_LABELS in the same edit."
    )


def test_the_worker_prompt_carries_no_forbidden_channel_spelling(prompt_text: str) -> None:
    """CS-1104: the prompt never names the sender, the ack flag or the writing watcher."""
    found = present(prompt_text, FORBIDDEN)

    assert found == [], f"{PROMPT_PATH} carries {found}; a lane cycle surfaces and never replies"


def test_a_document_carrying_every_forbidden_spelling_is_reported_for_each() -> None:
    """NEGATIVE CONTROL: the arm above reads a clean file, so the predicate must be seen to fire.

    Each spelling sits on its own line so that no one pattern's match can stand
    in for another's.
    """
    dirty = (
        "python tools/inbox_watch.py --ack\n"
        "then run tools/outbound_send.py\n"
        "after tools/outbound_gate.py grades it\n"
        "then python -m ops.loop.inbox_surface\n"
        "  inbox: 3 names\n"
    )

    assert present(dirty, FORBIDDEN) == [label for label, _pattern in FORBIDDEN]


def test_a_clean_document_carries_no_forbidden_spelling() -> None:
    """The other half: the predicate does not fire on the words the prompt DOES use."""
    clean = "surfacing never acknowledges; the driver surfaces the channel.\n"

    assert present(clean, FORBIDDEN) == []


def test_the_forbidden_table_matches_its_pin() -> None:
    """Deleting a forbidden spelling to green the arm above is caught here."""
    assert frozenset(label for label, _pattern in FORBIDDEN) == FORBIDDEN_LABELS


# --- CS-1104 W3: the fence sentences are BOUND to their paragraph, and nothing
# --- anywhere in the prompt instructs an acknowledgement or a reply.

#: The paragraph that carries the channel fence. Found by its step marker, so a
#: keyword surviving in some other paragraph does not satisfy the binding.
CHANNEL_STEP: Final = "**4f."

#: Words that turn a sentence into a REPORT of a claim rather than the claim. A
#: fence sentence carrying one of them is a retired draft wearing the keywords.
HEDGES: Final = re.compile(
    r"\b(draft|retired|claimed|older|formerly|used\s+to|no\s+longer|superseded|once\s+said)\b",
    re.IGNORECASE,
)

#: A sentence about the channel ...
CHANNEL_NOUN: Final = re.compile(
    r"moon_sync_inbox|\bchannel\b|\binbox\b|\bnotes?\b|\bitems?\b|\bsibling", re.IGNORECASE
)
#: ... that names an acknowledging or replying act ...
REPLY_VERB: Final = re.compile(
    r"\backnowledg\w*|\brepl(y|ies|ied|ying)\b|\banswer\w*|\brespond\w*|\bcompos\w*"
    r"|\bdeliver\w*|\bsend\w*|\bmark\w*\s+\w+\s+seen\b",
    re.IGNORECASE,
)
#: ... must carry a negation, or it is an instruction to do the act.
NEGATION: Final = re.compile(
    r"\bnever\b|\bnot\b|\bno\b|\bnothing\b|\bnor\b|out\s+of\s+scope|n't\b", re.IGNORECASE
)


def sentences(text: str) -> list[str]:
    """The text as whitespace-normalised sentences, split at . ; : and ! and ?."""
    flat = " ".join(text.split())
    return [part for part in re.split(r"(?<=[.;:!?])\s+", flat) if part]


def channel_paragraph(text: str) -> str:
    """The paragraph opened by :data:`CHANNEL_STEP`, up to the next blank line or heading."""
    start = text.find(CHANNEL_STEP)
    if start < 0:
        return ""
    rest = text[start:]
    end = re.search(r"\n\s*\n|\n#", rest)
    return rest if end is None else rest[: end.start()]


def binding_faults(text: str) -> list[str]:
    """Why the channel fence is NOT stated as live sentences of its own paragraph.

    Returns:
        Empty when the paragraph has a sentence OPENING with "Surfacing never
        acknowledges" and a sentence OPENING with "Composing" that places the act
        out of scope for a lane cycle, neither of them hedged.
    """
    paragraph = channel_paragraph(text)
    if not paragraph:
        return ["no channel step paragraph"]
    faults: list[str] = []
    parts = sentences(paragraph)
    ack = [p for p in parts if re.match(r"surfacing\s+never\s+acknowledges\b", p, re.IGNORECASE)]
    scope = [
        p
        for p in parts
        if re.match(r"composing\b", p, re.IGNORECASE)
        and re.search(r"out\s+of\s+scope\s+for\s+a\s+lane\s+cycle", p, re.IGNORECASE)
    ]
    if not ack:
        faults.append("no sentence opens with the never-acknowledges fence")
    if not scope:
        faults.append("no sentence opens with the composing-is-out-of-scope fence")
    faults += [f"hedged fence sentence: {p!r}" for p in ack + scope if HEDGES.search(p)]
    return faults


def reply_instructions(text: str) -> list[str]:
    """Every sentence that names the channel and an ack or reply act WITHOUT a negation."""
    return [
        p
        for p in sentences(text)
        if CHANNEL_NOUN.search(p) and REPLY_VERB.search(p) and not NEGATION.search(p)
    ]


#: The measured M6 mutant: an instruction to acknowledge and reply, with the fence
#: keywords kept alive inside a sentence that reports them as a retired draft.
RETIRED_DRAFT: Final = (
    "**4f. The cross-repo channel.** Acknowledge each item once you have surfaced it, and "
    "answer any item that asks for a reply. An older draft claimed surfacing never "
    "acknowledges and that composing a reply was not something to deliver; that draft "
    "called it out of scope for a lane cycle, and it is retired.\n\nNext paragraph.\n"
)


def test_the_channel_fence_is_bound_to_its_own_paragraph(prompt_text: str) -> None:
    """W3: the fence sentences open their own sentences inside step 4f, unhedged."""
    assert binding_faults(prompt_text) == []


def test_no_sentence_in_the_prompt_instructs_an_ack_or_a_reply(prompt_text: str) -> None:
    """W3: anywhere in the prompt, a channel sentence naming an ack or reply act is negated."""
    assert reply_instructions(prompt_text) == []


def test_control_a_retired_draft_fails_both_channel_predicates() -> None:
    """NEGATIVE CONTROL: the measured M6 text is reported by BOTH predicates above."""
    assert binding_faults(RETIRED_DRAFT), "the binding predicate passed a retired draft"
    assert reply_instructions(RETIRED_DRAFT), "the instruction predicate missed the ack order"


def test_control_the_live_fence_shape_passes_both_channel_predicates() -> None:
    """POSITIVE CONTROL: a minimal correct paragraph is reported for nothing."""
    good = (
        "**4f. The channel.** The driver surfaces moon_sync_inbox/ into its ledger. "
        "Surfacing never acknowledges: nothing marks an item seen. Composing, grading or "
        "delivering a note is out of scope for a lane cycle.\n\nNext.\n"
    )
    assert binding_faults(good) == []
    assert reply_instructions(good) == []
