#!/usr/bin/env python3
"""CS-860 - four personal-data classes derived from CLAUDE.md, two of them covered.

WHAT THIS MODULE GRADES, AND THE SHAPE IS NOT WHAT IT WAS. tests/conftest.py's
report redactor serves TWO of the four kinds of personal data CLAUDE.md names -
a home path, in five spellings, and the account name. The other two - the
platform account id and the world name - are REGISTERED AND UNCOVERED, declared
in that module's UNCOVERED_CLASSES with a reason each. So the arms below grade
three separate things: that the demanded SET still comes out of CLAUDE.md at
four, that every COVERED class is covered BEHAVIOURALLY rather than by
declaration, and that every UNCOVERED class is genuinely unserved rather than
quietly claimed.

WHY TWO ARE UNCOVERED, stated here because a reader meets this file before any
ledger. CS-860 first shipped SHAPE rules for both, built on a path-segment
character class borrowed from clockspeed/data/locate.py - where that class is
CORRECT, because locate.redact receives PATHS. redact_personal_data receives
WHOLE FAILURE REPORTS, which are arbitrary prose, and the same class was
measured destructive in both directions at once: `Some Save Name.sav` rendered
as `Some Save <redacted-save>`, leaking the world name it existed to hide, while
`workdir.py:120: in copy_for_read(World.sav)` rendered as `workdir.py:120: in
<redacted-save>)`, erasing a function name from a traceback frame line. The two
ends are one knob, so the rules were backed out rather than tuned. Both
counter-examples are PINNED by the uncovered arms below, so a rebuilt rule has
to answer them before it ships.

THE HOME WIDENING STAYED, and it is what the item's title was actually about.
OSError.__str__ renders filename through %r, which DOUBLES every backslash, so
the doubled spelling is what a chained cause prints - and before the widening it
missed the home rule entirely, caught only by the weaker account-name rule. That
containment holds on this machine solely because the account name happens to be
the only personal component of the home prefix. A naming accident is not a
control.

TWO GRADING DEFECTS WERE CLOSED HERE, both found by MUTATION rather than by
reading, and both are the same fault one level up: an arm that measures a NAME
where it should measure a BEHAVIOUR.

  - THE ESCAPED SPELLINGS WERE UNGRADED. One arm named the doubled spelling and
    none named either URL-quoted one, so DELETING `quote` from the transforms
    left the whole suite GREEN. The reason is exactly the naming accident above,
    reproduced inside the guard written to prevent it: MEASURED on this machine,
    the ACCOUNT-NAME rules alone rewrite all five home spellings and yield the
    account placeholder for every one of them, so a leak scan is satisfied
    whatever the home rules do. The repair is one arm PER SPELLING that applies
    ONLY the rules tagged home-path and demands the HOME placeholder
    specifically.

  - REGISTRATION IMPLIED NOTHING. Occupying a tuple slot satisfied
    test_every_registered_class_contributes_a_compiled_rule, and a function-name
    substring satisfied test_every_registered_class_has_a_named_arm. Neither
    asked whether a rule MATCHES anything, so a class registered with
    re.compile("(?!)") and a pass-bodied arm passed both. A corroborating probe
    SWAPPED the class tags between two rules and every arm stayed green, so the
    tags were decorative. The repair is that COVERAGE IS BEHAVIOURAL: a covered
    class must have rules TAGGED WITH IT that, applied ALONE, rewrite a planted
    string of that class into that class's OWN placeholder. A hollow rule
    produces no placeholder and a swapped tag produces the wrong one.

DERIVED RATHER THAN LISTED, which is the wording of the acceptance and the
whole point of the oracle below. Nothing here writes down "the four classes".
The demanded set is read out of CLAUDE.md on every run, from TWO independently
worded regions - section 2's save-directory paragraph and non-negotiable 3 -
and the arms go red when either region names something no registered class
claims, when the classes and either region's phrases are not ONE-TO-ONE, when a
class is declared neither covered nor uncovered, when a COVERED class's own
tagged rules rewrite nothing, when an UNCOVERED class turns out to be served
after all, when a class has no named arm here, or when a class id is spelled by
no phrase that claims it. Two independently worded
regions have to be defeated together to shrink the demanded set. The house
precedent for the shape is tools/drift_guard.py's work-item anchor: find the
sentence at run time, report rather than pass when it is absent, and count what
the sentence names independently of how its clauses are phrased.

THE BIJECTION IS THERE BECAUSE THE COVERING FORM WAS ATTACKED AND FELL. This
arm first asked only whether every class was claimed SOMEWHERE in each region.
Measured against a CLAUDE.md carrying a fifth class and a matcher widened by one
alternation to swallow it: every arm went GREEN while nothing redacted the new
class. Demanding one phrase per class and one class per phrase, per region,
defeats that move - the widened matcher then claims two phrases in one region
and the counts stop lining up.

WHAT THE ORACLE DELIBERATELY DOES NOT READ, stated rather than left implied.
Section 2's paragraph carries a middle sentence enumerating ARTIFACTS - a
tracked file, a commit message, a log, a fixture, a test - rather than classes.
It is excluded by construction: the two anchors are the "is personal data"
claim and the "The same applies to" extension, and that sentence is neither.
MEASURED, not predicted: a fifth class added to that middle sentence ALONE
leaves every arm here GREEN, while the same class added to either anchored
region turns them RED and names the phrase. That residual is stated rather than
papered over, and the repair for it is a class named in one of the two anchored
regions, which is where a non-negotiable belongs anyway.

THE PROVING RUN IS A CONFIGURED ONE, AND THAT IS THE TRAP CS-855 RECORDED. A
run whose rootdir is a tempdir loads neither pyproject.toml nor
tests/conftest.py, so it measures an unconfigured pipeline and proves nothing.
The sandbox therefore gets a BYTE-IDENTICAL COPY of the repository's
pyproject.toml, verified by sha256, and the run is asserted configured three
independent ways - the ``configfile:`` header line, the sha256 equality, and a
BEHAVIOURAL consequence of the config's contents.

THE BEHAVIOURAL FACT IS ``xfail_strict``, AND THE ONE THIS MODULE WAS BRIEFED TO
USE WAS MEASURED FALSE. The brief named the ``short test summary info`` banner,
"which only the config's ``-ra`` addopt produces". Measured across four arms:
that banner is present in an UNCONFIGURED run with no flags at all, because
pytest's default ``-r`` already reports failures. As evidence of configuration
it is vacuous - it would pass identically in exactly the run CS-855 warns
about. What replaced it is ``xfail_strict = true``: a sandbox test marked xfail
that PASSES is reported ``1 xpassed`` unconfigured and ``FAILED ...
[XPASS(strict)]`` under the copied config. That cannot be produced without the
config's contents.

WHY NOT ``-c <repo>/pyproject.toml``. Measured: 0.46s for the copied config
against 34.78s for ``-c``, which is the CS-448 rootdir-climb. Under the copy,
ROOTDIR IS THE SANDBOX rather than the repository - and ``testpaths`` is the
only rootdir-relative option in that config, inert here because the run is
given an explicit argument.

THREE MECHANISMS, ALL LANDING IN ``report.longrepr``, and they were chosen
because they escape their payload DIFFERENTLY - measured, not assumed. A chained
cause renders through ``OSError.__str__``, which is ``%r`` and therefore DOUBLES
every backslash. A rewritten assert renders the string diff RAW, so the
single-separator spelling appears. A callee frame argument renders through
``saferepr``, which doubles AND truncates the middle of a long value. An
``OSError`` used as the frame-argument carrier renders NOTHING, because
``repr(OSError)`` omits ``filename``, so the carrier here takes plain strings.

THE NEEDLES ARE SYNTHETIC WHERE THEY CAN BE AND REAL WHERE THEY MUST BE. The
account id and the save filename are invented values planted into the sandbox
source. They are STILL PLANTED although their classes are now uncovered, and
deliberately so: the control arm measures that they reach a rendered report,
which is what makes the declared gap a MEASURED fact rather than a claim. The
home path and the account name cannot be synthetic - the rules for them are
literal spellings of THIS machine - so they are derived inside the sandbox at
run time and are NEVER written into a tracked file and NEVER printed. Every
failure message below reports LABELS and COUNTS.

THE CONTROLS ARE THE HALF THAT MAKES THE REST MEAN ANYTHING. An unguarded twin
carries the same needles and must show a nonzero hit count PER MECHANISM BLOCK
per class, not merely over the whole region; both arms must have DETECTED
rather than crashed; and the guarded report must be REDACTED RATHER THAN
DELETED - every placeholder present, exception type names and
mechanism-identifying text still standing - so a remedy that blanks the report
cannot pass here.

STATED LIMITS.
  - The graded region is the run tail from the FAILURES banner on, minus
    pytest's warnings summary, borrowed from tests/test_tmp_path_privacy.py
    rather than respelled. The session header, which names the sandbox root, is
    outside it; that boundary is owned and measured by that module.
  - Home-path coverage is bounded at ONE escaping level, matching the bound the
    rules themselves declare. A quadrupled spelling - a repr of a repr - and
    the compositions of quoting with doubling are outside both.
  - THE WORLD NAME AND THE ACCOUNT ID ARE UNCOVERED IN EVERY FORM, not merely
    in their bare form. The bare form was always out of reach - operator-
    authored free text derivable from nothing on this machine, and that half
    belongs to CS-850 and CS-851 - but since the backout the marker-bearing and
    suffix-bearing forms are uncovered too. The arms below assert that gap
    rather than papering it, so it cannot close by accident or widen in silence.
  - A PER-SPELLING HOME ARM IS ONLY A CONTROL WHERE THE SPELLINGS DIFFER. On a
    platform that writes no backslash and quotes no separator, several of the
    five spellings are byte-identical, and deleting a transform there is an
    EQUIVALENT mutant rather than a surviving one. Those arms SKIP loudly and
    name the platform limit rather than passing quietly.
  - The rule set is NOT enumerated from the live save directory, which would be
    legal and is deliberately not done: it would make the rules
    environment-dependent, so a green run here would say nothing about CI.
"""

from __future__ import annotations

import ast
import getpass
import hashlib
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Iterator, Mapping
from pathlib import Path
from urllib.parse import quote

import pytest

from clockspeed.data.locate import SAVE_ROOT_PARTS
from tests import conftest as shipped
from tests.conftest import (
    REDACTED_HOME,
    REDACTED_USER,
    redact_personal_data,
)
from tests.test_tmp_path_privacy import (
    PYTEST_TESTS_FAILED,
    REPO_ROOT,
    SANDBOX_CONFTEST,
    SUBPROCESS_TIMEOUT,
    SandboxRun,
    failure_blocks,
    guarded_region,
)

# ---------------------------------------------------------------------------
# The registry, read off the shipped module rather than written down here
# ---------------------------------------------------------------------------

#: Every personal-data class tests/conftest.py declares, derived from its
#: namespace. Reading the namespace rather than importing four names by hand is
#: what makes a fifth class arriving there VISIBLE to the arms below instead of
#: silently unmeasured.
REGISTERED_CLASSES: tuple[str, ...] = tuple(
    sorted(
        value
        for name, value in vars(shipped).items()
        if name.startswith("CLASS_") and isinstance(value, str)
    )
)

#: What tests/conftest.py DECLARES about each class. Read off the shipped
#: module rather than restated, for the same reason REGISTERED_CLASSES is: a
#: class moving between the two must be VISIBLE here rather than silent.
COVERED_CLASSES: frozenset[str] = shipped.COVERED_CLASSES
UNCOVERED_CLASSES: Mapping[str, str] = shipped.UNCOVERED_CLASSES

#: The placeholder each COVERED class's rules substitute. Used as that class's
#: FINGERPRINT: its absence means the rules did not run, which is the half a
#: leak scan alone cannot see - measured on this machine, the account-name
#: rules alone rewrite all five home spellings, so deleting the home rules
#: leaves nothing recognisable for a scan to find. AN UNCOVERED CLASS HAS NO
#: FINGERPRINT, and an arm below asserts this map's domain is exactly the
#: covered set, so a class cannot arrive in one without the other.
CLASS_FINGERPRINTS: dict[str, str] = {
    shipped.CLASS_HOME_PATH: REDACTED_HOME,
    shipped.CLASS_ACCOUNT_NAME: REDACTED_USER,
}

#: The five home spellings graded one arm each. Held as static labels so
#: parametrisation never calls Path.home() at collection; an arm asserts they
#: are exactly the labels _home_spellings() produces, so the list cannot drift.
HOME_SPELLING_LABELS: tuple[str, ...] = (
    "home-native",
    "home-posix",
    "home-doubled",
    "home-quoted-native",
    "home-quoted-posix",
)

#: The shortest exemption this suite will accept as a reason. A registered
#: exemption carrying an empty string is the silence the registry exists to
#: prevent, wearing the registry's clothes.
MIN_REASON_WORDS = 12

#: How a phrase in CLAUDE.md is recognised as naming a class. This is the ONLY
#: authored half of the derivation: the SET of classes is demanded by the
#: document, and a phrase no matcher claims is a red rather than a shrug.
CLASS_PHRASE_MATCHERS: dict[str, re.Pattern[str]] = {
    shipped.CLASS_HOME_PATH: re.compile(r"\bhome\b", re.IGNORECASE),
    shipped.CLASS_ACCOUNT_NAME: re.compile(r"\bwindows\b", re.IGNORECASE),
    shipped.CLASS_ACCOUNT_ID: re.compile(r"\baccount\s+id\b", re.IGNORECASE),
    shipped.CLASS_WORLD_NAME: re.compile(r"\bworld\s+name\b", re.IGNORECASE),
}

# ---------------------------------------------------------------------------
# The two CLAUDE.md regions, located by anchor at run time
# ---------------------------------------------------------------------------

CLAUDE_MD = REPO_ROOT / "CLAUDE.md"

#: The personal-data STATUS claim in section 2. An anchor, not a restatement -
#: it names no class, and the arm reports rather than passes when it is absent.
ANCHOR_STATUS_CLAIM = "is personal data"

#: The extension marker that carries the rest of section 2's classes. Also
#: names no class.
ANCHOR_EXTENSION = "The same applies to"

#: Non-negotiable 3, located STRUCTURALLY - a numbered item beginning with the
#: prohibition verb. "Never hardcode" alone appears twice in CLAUDE.md; only one
#: of the two is a numbered non-negotiable.
NON_NEGOTIABLE_LINE = re.compile(r"^\d+\.\s+Never hardcode\b(?P<body>.*)$", re.MULTILINE)

#: How an enumeration is split into phrases, independently of whether its
#: clauses are joined by commas, "and" or "or".
_ENUMERATION_SPLIT = re.compile(r"\s*,\s*|\s+and\s+|\s+or\s+")

#: A leading conjunction left behind when a comma and a conjunction both sit
#: between two items - "a, b, or c".
_LEADING_CONJUNCTION = re.compile(r"^(?:and|or)\s+", re.IGNORECASE)

#: Markdown emphasis and code fencing, removed before sentences are split so a
#: bold span crossing a sentence boundary does not merge two sentences.
_MARKDOWN_NOISE = re.compile(r"[*`]")

#: A sentence boundary: a period followed by whitespace.
_SENTENCE_SPLIT = re.compile(r"(?<=\.)\s+")

# ---------------------------------------------------------------------------
# What gets planted. Path-shaped literals live at MODULE scope on purpose:
# tests/test_assertion_rendering.py sweeps FUNCTION BODIES for source lines
# pytest renders above a failing assertion, and a planted save path inside one
# would be reported as this machine's redactor recognising a path.
# ---------------------------------------------------------------------------

BACKSLASH = chr(92)

#: The save-root marker, DERIVED from the resolver's own parts rather than
#: spelled here, so a relocation moves the plant with the rule it exercises.
SAVE_ROOT_MARKER = "/".join(SAVE_ROOT_PARTS)

#: A digit-shaped synthetic account directory. Deliberately not a real Steam id
#: - those begin 7656119 - and deliberately not this machine's own.
PLANTED_ACCOUNT_ID = "90000000000000860"

#: A NON-DIGIT synthetic account directory, planted so a green run cannot be
#: explained by a digit-run rule. Epic writes a hex token in this position and
#: the Microsoft Store a braceless GUID, so a rule that only sees digits is
#: correct for one platform and silent for the other three.
PLANTED_ACCOUNT_HEX = "cs860a1b2c3d4e5f"

#: The world name a save file carries. The oracle scans for the STEM, so a rule
#: that stripped only the suffix would not satisfy it.
PLANTED_SAVE_STEM = "Cs860SyntheticWorld"
PLANTED_SAVE_FILE = PLANTED_SAVE_STEM + ".sav"

#: What brackets the account name in the sandbox. The bare account name cannot
#: be scanned for directly - on a CI runner it is ``runner``, an ordinary
#: English substring, and this project has already measured 33 false positives
#: from exactly that. The composite is unique to this module, so its survival
#: is unambiguous and its redaction leaves a string that no longer matches.
NAME_OPEN = "CS860["
NAME_CLOSE = "]860"

#: A home spelling shorter than this is a bare drive or filesystem root, which
#: is not personal data and would match half the output if it were scanned for.
MIN_HOME_SPELLING = 4

SANDBOX_TEST_FILENAME = "test_cs860_forced_failures.py"

CHAINED_CAUSE_TEST = "test_chained_cause_renders_every_needle"
REWRITTEN_ASSERT_TEST = "test_rewritten_assert_renders_every_needle"
FRAME_ARGUMENT_TEST = "test_callee_frame_argument_renders_every_needle"
XFAIL_STRICT_TEST = "test_xfail_strict_probe_passes"

MECHANISM_TESTS: tuple[str, ...] = (
    CHAINED_CAUSE_TEST,
    REWRITTEN_ASSERT_TEST,
    FRAME_ARGUMENT_TEST,
)

#: Every block the run must render. The xfail probe is one of them: its absence
#: would mean the config was not applied, not that nothing leaked.
EXPECTED_BLOCKS: tuple[str, ...] = (*MECHANISM_TESTS, XFAIL_STRICT_TEST)
EXPECTED_FAILURES = len(EXPECTED_BLOCKS)

#: Text a redaction must NOT delete. A remedy that blanked the report would
#: pass every leak scan in this file and be useless, so what has to SURVIVE is
#: asserted as explicitly as what has to go.
SURVIVING_FRAGMENTS: tuple[str, ...] = (
    "RuntimeError",
    "ValueError",
    "AssertionError",
    "CS-860 chained cause",
    "CS-860 callee frame argument",
    "XPASS(strict)",
)

SANDBOX_TESTS = '''
"""Synthetic module: three rendering mechanisms, each carrying every needle.

Written into a sandbox at run time. The home path and the account name are
derived HERE so this machine's own spellings never touch a tracked file; the
account directories and the save filename are synthetic and interpolated in.
"""

import getpass
from pathlib import Path
from urllib.parse import quote

import pytest

ACCOUNT_ID = "{account_id}"
ACCOUNT_HEX = "{account_hex}"
SAVE_FILE = "{save_file}"
MARKER = "{marker}"
NAME_OPEN = "{name_open}"
NAME_CLOSE = "{name_close}"
BS = chr(92)


def needles():
    """Every planted needle, in the spelling the mechanism will then escape."""
    home = str(Path.home())
    posix = Path.home().as_posix()
    return {{
        "home_native": home,
        "home_posix": posix,
        "home_quoted": quote(home),
        "home_quoted_posix": quote(posix),
        "account_name": NAME_OPEN + getpass.getuser() + NAME_CLOSE,
        "account_dir": MARKER + "/" + ACCOUNT_ID,
        "account_dir_windows": MARKER.replace("/", BS) + BS + ACCOUNT_HEX,
        "save_path": MARKER + "/" + ACCOUNT_ID + "/" + SAVE_FILE,
    }}


def carrier(
    home_native,
    home_posix,
    home_quoted,
    home_quoted_posix,
    account_name,
    account_dir,
    account_dir_windows,
    save_path,
):
    """A callee whose frame ARGUMENTS are what pytest renders.

    One parameter per needle rather than one joined string: pytest renders each
    argument through saferepr with its own size budget, and a single joined
    value is truncated THROUGH THE MIDDLE - measured, and it dropped a whole
    class out of this channel.
    """
    raise ValueError("CS-860 callee frame argument")


def test_chained_cause_renders_every_needle():
    try:
        raise OSError(2, "CS-860 planted cause", " ".join(needles().values()))
    except OSError as exc:
        raise RuntimeError("CS-860 chained cause") from exc


def test_rewritten_assert_renders_every_needle():
    rendered = " ".join(needles().values())
    assert rendered == "CS-860 rewritten assert"


def test_callee_frame_argument_renders_every_needle():
    carrier(**needles())


@pytest.mark.xfail(reason="CS-860 config probe - this passes on purpose")
def test_xfail_strict_probe_passes():
    assert True
'''


# ---------------------------------------------------------------------------
# The oracle. Derived at TEST time, never at conftest import - a document read
# at import would make a renamed CLAUDE.md an unimportable conftest, which is a
# suite that does not start.
# ---------------------------------------------------------------------------


def _claude_md_text() -> str:
    """CLAUDE.md, or a loud failure naming the file that was not there."""
    if not CLAUDE_MD.is_file():
        pytest.fail(
            "the personal-data derivation reads CLAUDE.md and it is not at the "
            "path this module derives from the repository root. The classes "
            "cannot be derived, so nothing below can be graded"
        )
    return CLAUDE_MD.read_text(encoding="utf-8")


def _sentences(paragraph: str) -> list[str]:
    """One paragraph split into sentences, markdown emphasis removed first."""
    flat = " ".join(_MARKDOWN_NOISE.sub("", paragraph).split())
    return [part.strip() for part in _SENTENCE_SPLIT.split(flat) if part.strip()]


def _paragraph_containing(text: str, anchor: str) -> str | None:
    """The blank-line-delimited paragraph holding ``anchor``, or None."""
    for paragraph in text.split("\n\n"):
        if anchor in paragraph:
            return paragraph
    return None


def _enumerated(phrase: str) -> tuple[str, ...]:
    """Split an enumeration into its items, however its clauses are joined."""
    items = []
    for raw in _ENUMERATION_SPLIT.split(phrase.strip().rstrip(".")):
        cleaned = _LEADING_CONJUNCTION.sub("", raw.strip()).strip().rstrip(".")
        if cleaned:
            items.append(cleaned)
    return tuple(items)


def _section_two_phrases(text: str) -> tuple[str, ...] | None:
    """Section 2's personal-data phrases, from its two class-naming sentences.

    Two anchors, neither of which names a class. The STATUS CLAIM sentence
    ("It is personal data ...") refers back to the sentence before it, which is
    where the account directory is named; the EXTENSION sentence ("The same
    applies to ...") carries the rest. The sentence between them enumerates
    artifacts rather than classes and is outside both anchors by construction -
    that exclusion is a stated residual in this module's docstring.

    Returns:
        The phrases, or None when either anchor is missing.
    """
    paragraph = _paragraph_containing(text, ANCHOR_STATUS_CLAIM)
    if paragraph is None or ANCHOR_EXTENSION not in paragraph:
        return None
    sentences = _sentences(paragraph)
    claim_index = next(
        (index for index, item in enumerate(sentences) if ANCHOR_STATUS_CLAIM in item), -1
    )
    extension = next((item for item in sentences if ANCHOR_EXTENSION in item), None)
    if claim_index < 1 or extension is None:
        return None
    subject = sentences[claim_index - 1]
    if " is " not in subject:
        return None
    named = subject.rsplit(" is ", 1)[1]
    tail = extension.split(ANCHOR_EXTENSION, 1)[1]
    return (*_enumerated(named), *_enumerated(tail))


def _non_negotiable_phrases(text: str) -> tuple[str, ...] | None:
    """Non-negotiable 3's enumeration, read exhaustively, or None if absent."""
    match = NON_NEGOTIABLE_LINE.search(text)
    return None if match is None else _enumerated(match.group("body"))


def _claiming_classes(phrase: str) -> tuple[str, ...]:
    """Every registered class whose matcher claims ``phrase``."""
    return tuple(
        class_id
        for class_id, matcher in CLASS_PHRASE_MATCHERS.items()
        if matcher.search(phrase) is not None
    )


@pytest.fixture(scope="module")
def claude_md_regions() -> dict[str, tuple[str, ...]]:
    """The two independently worded regions, as phrase tuples."""
    text = _claude_md_text()
    return {
        "section-2": _section_two_phrases(text) or (),
        "non-negotiable-3": _non_negotiable_phrases(text) or (),
    }


# ---------------------------------------------------------------------------
# The proving run
# ---------------------------------------------------------------------------


def _sha256(path: Path) -> str:
    """The file's digest, read as bytes so no newline translation applies."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_sandbox(root: Path, *, guarded: bool) -> Path:
    """Write the synthetic module, the copied config, and the redaction if guarded."""
    root.mkdir(parents=True, exist_ok=True)
    source = SANDBOX_TESTS.format(
        account_id=PLANTED_ACCOUNT_ID,
        account_hex=PLANTED_ACCOUNT_HEX,
        save_file=PLANTED_SAVE_FILE,
        marker=SAVE_ROOT_MARKER,
        name_open=NAME_OPEN,
        name_close=NAME_CLOSE,
    )
    (root / SANDBOX_TEST_FILENAME).write_bytes(source.encode("ascii"))
    shutil.copyfile(REPO_ROOT / "pyproject.toml", root / "pyproject.toml")
    if guarded:
        conftest = SANDBOX_CONFTEST.format(repo_root=str(REPO_ROOT))
        (root / "conftest.py").write_bytes(conftest.encode("ascii"))
    return root


def _run_sandbox(root: Path, label: str) -> SandboxRun:
    """Run pytest on the sandbox with NO flags - the config is the copied file.

    ``-c`` is deliberately not used. Measured, it costs 34.78s against 0.46s
    here, because pointing ``-c`` at the repository's own config makes pytest
    climb from the repository root (CS-448). The copy puts the rootdir in the
    sandbox instead, where ``testpaths`` - the config's only rootdir-relative
    option - is inert because the run is given an explicit argument.
    """
    env = dict(os.environ)
    for name in ("PYTEST_ADDOPTS", "PYTEST_CURRENT_TEST", "PYTEST_DEBUG_TEMPROOT", "PYTHONPATH"):
        env.pop(name, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", SANDBOX_TEST_FILENAME],
        cwd=str(root),
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=SUBPROCESS_TIMEOUT,
        check=False,
    )
    return SandboxRun(label, completed.returncode, completed.stdout + completed.stderr)


@pytest.fixture(scope="module")
def guarded_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The guarded sandbox directory, kept so its config copy can be hashed."""
    return _build_sandbox(tmp_path_factory.mktemp("cs860_guarded"), guarded=True)


@pytest.fixture(scope="module")
def control_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The unguarded twin's directory."""
    return _build_sandbox(tmp_path_factory.mktemp("cs860_control"), guarded=False)


@pytest.fixture(scope="module")
def guarded_run(guarded_root: Path) -> SandboxRun:
    """The shipped redaction installed, under the copied configuration."""
    return _run_sandbox(guarded_root, "guarded")


@pytest.fixture(scope="module")
def control_run(control_root: Path) -> SandboxRun:
    """The same sandbox with NO redaction - the proof this harness can fail."""
    return _run_sandbox(control_root, "control")


def _home_spellings() -> dict[str, str]:
    """This machine's home directory in the five spellings the rules cover.

    Derived HERE rather than borrowed from the redactor. A redactor is blind
    exactly where it is blind, so it can never be its own oracle. Bounded at
    one escaping level, which is the bound the rules themselves declare.
    """
    home = str(Path.home())
    posix = Path.home().as_posix()
    return {
        "home-native": home,
        "home-posix": posix,
        "home-doubled": home.replace(BACKSLASH, BACKSLASH * 2),
        "home-quoted-native": quote(home),
        "home-quoted-posix": quote(posix),
    }


def _class_needles() -> dict[str, dict[str, str]]:
    """Every scanned spelling, per class, keyed by a label safe to print."""
    return {
        shipped.CLASS_HOME_PATH: _home_spellings(),
        shipped.CLASS_ACCOUNT_NAME: {
            "account-name-composite": NAME_OPEN + getpass.getuser() + NAME_CLOSE
        },
        shipped.CLASS_ACCOUNT_ID: {
            "account-id-decimal": PLANTED_ACCOUNT_ID,
            "account-id-hex": PLANTED_ACCOUNT_HEX,
        },
        shipped.CLASS_WORLD_NAME: {"world-name-stem": PLANTED_SAVE_STEM},
    }


def _redact_with_only(text: str, class_id: str) -> str:
    """Apply ONLY the rules TAGGED with ``class_id``, in their shipped order.

    THE SUBSET IS THE WHOLE POINT, AND IT WAS MEASURED. Applying the full rule
    set cannot attribute a redaction to a class: on this machine the
    ACCOUNT-NAME rules alone rewrite every one of the five home spellings and
    yield the account placeholder for each. So a home arm run against the full
    set - or any arm that merely scans for a leak - is satisfied whatever the
    home rules do, which is how deleting a transform survived the earlier form
    of this module. Grading a class through its own tagged subset is what
    removes that, and it is also what makes a SWAPPED tag visible: the rules
    still fire, but they produce the wrong class's placeholder.

    Args:
        text: The string to redact.
        class_id: The class whose rules alone are applied.

    Returns:
        The text with only that class's substitutions applied.
    """
    for pattern, replacement, tag in shipped._REDACTION_RULES:  # noqa: SLF001
        if tag == class_id:
            text = pattern.sub(replacement, text)
    return text


def _surviving_labels(text: str, needles: dict[str, str]) -> list[str]:
    """Which needle LABELS are present in ``text``. Never returns a value."""
    return sorted(label for label, value in needles.items() if value in text)


def _assert_home_oracle_is_not_vacuous() -> None:
    """Refuse to grade the home class on a machine whose home is a bare root."""
    length = len(str(Path.home()))
    assert length >= MIN_HOME_SPELLING, (
        f"this machine's home path is {length} characters, which is a bare "
        "root rather than personal data - the home arm below would be vacuous"
    )


# ---------------------------------------------------------------------------
# The derivation - CLAUDE.md demands the class set, this module does not
# ---------------------------------------------------------------------------


def test_both_claude_md_regions_are_present_and_non_empty(claude_md_regions):
    empty = sorted(name for name, phrases in claude_md_regions.items() if not phrases)
    assert empty == [], (
        f"the personal-data derivation could not read {empty} out of CLAUDE.md. "
        "An anchor sentence has moved or been reworded, so the demanded class "
        "set is unknown and nothing below is graded rather than green"
    )


def test_every_phrase_claude_md_names_is_claimed_by_exactly_one_class(claude_md_regions):
    unclaimed: list[str] = []
    ambiguous: list[str] = []
    for region, phrases in claude_md_regions.items():
        for phrase in phrases:
            claims = _claiming_classes(phrase)
            if not claims:
                unclaimed.append(f"{region}: {phrase}")
            elif len(claims) > 1:
                ambiguous.append(f"{region}: {phrase} -> {sorted(claims)}")
    assert unclaimed == [], (
        "CLAUDE.md names personal data that no registered class claims. The "
        "redactor is therefore blind to it by construction: "
        f"{sorted(unclaimed)}"
    )
    assert ambiguous == [], (
        "a phrase is claimed by more than one class, so which rules serve it "
        f"is not determined: {sorted(ambiguous)}"
    )


def test_every_registered_class_is_claimed_exactly_once_in_each_region(claude_md_regions):
    # A BIJECTION, NOT A COVERING, AND THE DIFFERENCE WAS MEASURED. A covering
    # test - "every class is claimed somewhere in this region" - is satisfied by
    # WIDENING a matcher: add a fifth class to CLAUDE.md, widen an existing
    # matcher until it swallows the new phrase, and every arm goes green while
    # nothing redacts it. That attack was run against the covering form of this
    # arm and it SUCCEEDED. Demanding one phrase per class and one class per
    # phrase defeats it, because the widened matcher then claims two phrases in
    # the same region and the counts no longer line up.
    faults: list[str] = []
    for region, phrases in claude_md_regions.items():
        counts = dict.fromkeys(REGISTERED_CLASSES, 0)
        for phrase in phrases:
            for class_id in _claiming_classes(phrase):
                if class_id in counts:
                    counts[class_id] += 1
        faults.extend(
            f"{region}: {class_id} claimed by {count} phrases"
            for class_id, count in sorted(counts.items())
            if count != 1
        )
        if len(phrases) != len(REGISTERED_CLASSES):
            faults.append(
                f"{region}: names {len(phrases)} kinds of personal data while "
                f"{len(REGISTERED_CLASSES)} classes are registered"
            )
    assert faults == [], (
        "CLAUDE.md and the registered classes are no longer one-to-one in each "
        "region. Two independently worded regions have to agree for the "
        "demanded set to be trusted, and a class claimed twice in one region is "
        f"a matcher wide enough to hide a third: {sorted(faults)}"
    )


def test_every_registered_class_id_is_spelled_by_a_phrase_that_claims_it(claude_md_regions):
    all_phrases = [phrase for phrases in claude_md_regions.values() for phrase in phrases]
    unspelled: list[str] = []
    for class_id in REGISTERED_CLASSES:
        tokens = [token for token in class_id.split("-") if token]
        claiming = [p.lower() for p in all_phrases if class_id in _claiming_classes(p)]
        if not any(all(token in phrase for token in tokens) for phrase in claiming):
            unspelled.append(class_id)
    assert unspelled == [], (
        "a class id is not spelled by any phrase that claims it, so renaming "
        "the id would leave the mapping true and the derivation meaningless: "
        f"{sorted(unspelled)}"
    )


def _served_classes() -> set[str]:
    """Every class id some compiled rule is tagged with."""
    return {class_id for _pattern, _replacement, class_id in shipped._REDACTION_RULES}  # noqa: SLF001


def test_every_registered_class_is_declared_covered_or_uncovered():
    # THE PARTITION, AND IT IS WHAT STOPS A CLASS BEING QUIETLY DROPPED. Backing
    # a rule out is legitimate; letting its class evaporate from the registry is
    # not, because a gap nothing names is a gap nothing checks.
    declared = set(COVERED_CLASSES) | set(UNCOVERED_CLASSES)
    registered = set(REGISTERED_CLASSES)
    undeclared = sorted(registered - declared)
    assert undeclared == [], (
        f"a registered class is declared neither covered nor uncovered: {undeclared}. "
        "Every class must state which it is, because 'uncovered' is a fact this "
        "suite checks and silence is not"
    )
    unregistered = sorted(declared - registered)
    assert unregistered == [], (
        f"a coverage declaration names a class that is not registered: {unregistered}"
    )
    both = sorted(set(COVERED_CLASSES) & set(UNCOVERED_CLASSES))
    assert both == [], f"a class is declared covered AND uncovered: {both}"


def test_the_fingerprint_map_covers_exactly_the_covered_classes():
    missing = sorted(class_id for class_id in COVERED_CLASSES if class_id not in CLASS_FINGERPRINTS)
    assert missing == [], (
        f"a covered class has no placeholder fingerprint: {missing}. The "
        "behavioural arm grades a class by the placeholder its own rules "
        "produce, so a covered class without one cannot be graded at all"
    )
    stray = sorted(class_id for class_id in CLASS_FINGERPRINTS if class_id not in COVERED_CLASSES)
    assert stray == [], (
        f"an uncovered class carries a placeholder fingerprint: {stray}. A "
        "fingerprint is what a covered class has, so this is an uncovered class "
        "dressed as a covered one"
    )


def test_every_covered_class_contributes_a_compiled_rule():
    served = _served_classes()
    barren = sorted(class_id for class_id in COVERED_CLASSES if class_id not in served)
    assert barren == [], (
        f"a class is declared COVERED and no compiled rule serves it: {barren}. A "
        "declared class with no rule redacts nothing while reading as covered"
    )
    stray = sorted(class_id for class_id in served if class_id not in REGISTERED_CLASSES)
    assert stray == [], f"a rule is tagged with a class that is not registered: {stray}"


def test_no_uncovered_class_is_served_by_any_rule():
    # THE MIRROR OF THE ARM ABOVE, AND BOTH DIRECTIONS ARE NEEDED. This one
    # stops an UNCOVERED class from acquiring a rule quietly and so masquerading
    # as covered; the behavioural arm stops a COVERED class from going uncovered
    # in silence. Neither alone closes the pair.
    served = _served_classes()
    contradicted = sorted(class_id for class_id in UNCOVERED_CLASSES if class_id in served)
    assert contradicted == [], (
        f"a class is declared UNCOVERED and a rule is tagged with it anyway: "
        f"{contradicted}. The declaration and the rule set disagree - either the "
        "rule came back, in which case move the class to COVERED_CLASSES and let "
        "the behavioural arm grade it, or the tag is wrong"
    )


def test_every_covered_class_has_tagged_rules_that_rewrite_its_own_planted_string():
    # REGISTRATION IS NOT COVERAGE, AND THIS IS THE ARM THAT MAKES THE
    # DIFFERENCE. Two mutants were measured against the earlier form and BOTH
    # SURVIVED: a class registered with a never-matching rule plus a pass-bodied
    # arm, and a pair of rules with their class TAGS SWAPPED. Neither changes a
    # tuple slot or a function name, which is all the earlier arms read. Here a
    # class is graded through the rules TAGGED WITH IT, applied ALONE, and must
    # turn a planted string of its own class into its OWN placeholder - so a
    # hollow rule produces no placeholder, and a swapped tag produces another
    # class's.
    _assert_home_oracle_is_not_vacuous()
    needles = _class_needles()
    faults: list[str] = []
    for class_id in sorted(COVERED_CLASSES):
        fingerprint = CLASS_FINGERPRINTS[class_id]
        for label, probe in sorted(needles[class_id].items()):
            redacted = _redact_with_only(probe, class_id)
            if redacted == probe:
                faults.append(f"{class_id}/{label}: its own tagged rules rewrote nothing")
            elif fingerprint not in redacted:
                faults.append(f"{class_id}/{label}: rewritten without producing {fingerprint}")
    assert faults == [], (
        "a class is declared COVERED and its own rules do not demonstrably "
        f"redact it: {sorted(faults)}. Occupying a rule slot is not coverage - a "
        "rule that matches nothing, or one carrying another class's tag, holds "
        "the slot and redacts nothing of this class"
    )


def test_the_graded_home_spelling_labels_are_the_ones_the_oracle_produces():
    produced = sorted(_home_spellings())
    assert sorted(HOME_SPELLING_LABELS) == produced, (
        "the per-spelling arms are parametrised over a label list that no "
        f"longer matches the spellings the oracle derives: {produced}. A "
        "spelling with no arm is a transform with no control"
    )


@pytest.mark.parametrize("label", HOME_SPELLING_LABELS)
def test_each_home_path_spelling_reaches_the_home_rules_alone(label):
    # ONE ARM PER SPELLING, WHICH IS THE DEFECT THIS CLOSES. The earlier module
    # named the doubled spelling and neither URL-quoted one, so deleting `quote`
    # from the transforms left every arm green.
    _assert_home_oracle_is_not_vacuous()
    spellings = _home_spellings()
    spelling = spellings[label]
    twins = sorted(
        other for other, value in spellings.items() if other != label and value == spelling
    )
    if twins:
        pytest.skip(
            f"this platform spells {label} byte-identically to {twins}, so this "
            "arm is not a control on its own transform here: deleting that "
            "transform would leave the spelling covered by another, which is an "
            "EQUIVALENT mutant rather than a surviving one. The transform is "
            "UNMEASURED on this platform, not absent"
        )
    # BOUND TO A SCALAR - see the doubled-spelling arm below for the measured
    # reason. The value this compares is derived from the real home.
    reached_home_rules = REDACTED_HOME in _redact_with_only(spelling, shipped.CLASS_HOME_PATH)
    assert reached_home_rules, (
        f"the {label} home spelling did not reach the HOME rules. Only the rules "
        "TAGGED home-path were applied, deliberately: measured on this machine "
        "the account-name rules alone rewrite all five spellings and yield the "
        "account placeholder for every one, so an arm run against the whole rule "
        "set, or one that merely scans for a leak, is satisfied whatever the home "
        "rules do. That is the naming accident this item exists to remove"
    )


def _test_names_defined_here() -> Iterator[str]:
    """Every test function this module itself defines."""
    for name, value in globals().items():
        if name.startswith("test_") and callable(value) and value.__module__ == __name__:
            yield name


def test_every_registered_class_has_a_named_arm():
    names = list(_test_names_defined_here())
    armless = sorted(
        class_id
        for class_id in REGISTERED_CLASSES
        if not any(class_id.replace("-", "_") in name for name in names)
    )
    assert armless == [], (
        f"a registered class has no arm in this module naming it: {armless}. "
        "A class nothing grades is a class the next edit can break silently"
    )


# ---------------------------------------------------------------------------
# The rules themselves - the primitives, the restatement, and the freeze
# ---------------------------------------------------------------------------


def _module_level_assignments(tree: ast.Module) -> dict[str, list[ast.stmt]]:
    """Every module-level assignment, keyed by target name."""
    found: dict[str, list[ast.stmt]] = {}
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            found.setdefault(node.target.id, []).append(node)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found.setdefault(target.id, []).append(node)
    return found


#: Calls that would make the rule set depend on WHEN it was built. CS-428's
#: first build was refuted because a lazily seeded rule set was poisoned by
#: this suite's own environment monkeypatching, so a rule built from any of
#: these outside the one frozen derivation is the same defect returning.
FORBIDDEN_IN_STATIC_RULES = frozenset(
    {
        "environ",
        "getenv",
        "home",
        "expanduser",
        "gettempdir",
        "getuser",
        "getcwd",
        "glob",
        "iterdir",
        "listdir",
        "scandir",
        "resolve",
        "exists",
        "cache",
        "lru_cache",
    }
)

#: The module-scope constants the surviving rules are built from. Each must be
#: STATIC. The shape-rule names this tuple used to carry went out with the
#: rules; what is left is the home-spelling transforms and the account-name
#: boundary primitives, and the property they must hold is unchanged.
STATIC_RULE_NAMES: tuple[str, ...] = (
    "_PERCENT_ESCAPE",
    "_NAME_LEFT_BOUNDARY",
    "_NAME_RIGHT_BOUNDARY",
    "_BACKSLASH",
    "_HOME_SPELLING_TRANSFORMS",
)


def test_the_rule_constants_read_neither_the_environment_nor_the_filesystem():
    tree = ast.parse((REPO_ROOT / "tests" / "conftest.py").read_text(encoding="utf-8"))
    assignments = _module_level_assignments(tree)
    absent = sorted(name for name in STATIC_RULE_NAMES if name not in assignments)
    assert absent == [], (
        f"a rule constant this arm grades is not assigned at module scope: {absent}"
    )
    offending: list[str] = []
    for name in STATIC_RULE_NAMES:
        for node in assignments[name]:
            for inner in ast.walk(node):
                if isinstance(inner, ast.Attribute) and inner.attr in FORBIDDEN_IN_STATIC_RULES:
                    offending.append(f"{name}: .{inner.attr}")
                elif isinstance(inner, ast.Name) and inner.id in FORBIDDEN_IN_STATIC_RULES:
                    offending.append(f"{name}: {inner.id}")
    assert offending == [], (
        "a rule constant reads the environment or the filesystem at import. "
        "That is the CS-428 poisoning defect returning through a new door - the "
        f"constants the rules are built from must be static: {sorted(offending)}"
    )


def test_the_rule_set_name_is_assigned_exactly_once():
    tree = ast.parse((REPO_ROOT / "tests" / "conftest.py").read_text(encoding="utf-8"))
    at_module_scope = len(_module_level_assignments(tree).get("_REDACTION_RULES", []))
    anywhere = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign | ast.AnnAssign | ast.AugAssign)
        for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
        if isinstance(target, ast.Name) and target.id == "_REDACTION_RULES"
    )
    assert anywhere == 1, (
        f"_REDACTION_RULES is assigned {anywhere} times in tests/conftest.py. A "
        "second assignment, or any path that rebuilds the rules later, is the "
        "lazily seeded rule set that refuted CS-428's first build"
    )
    assert at_module_scope == 1, (
        f"_REDACTION_RULES has {at_module_scope} module-scope assignments. The "
        "freeze depends on it being computed once, at import, on the only path "
        "that reaches this module at all"
    )


# ---------------------------------------------------------------------------
# The proving run - configured, detected, and controlled
# ---------------------------------------------------------------------------


def test_the_proving_run_was_configured_by_the_shipped_pyproject(guarded_root, guarded_run):
    copied = guarded_root / "pyproject.toml"
    shipped_config = REPO_ROOT / "pyproject.toml"
    identical = copied.is_file() and _sha256(copied) == _sha256(shipped_config)
    facts = {
        "configfile-header": "configfile: pyproject.toml" in guarded_run.output,
        "sha256-identical": identical,
        "xfail-strict-behaviour": "XPASS(strict)" in guarded_run.output,
    }
    absent = sorted(name for name, held in facts.items() if not held)
    assert absent == [], (
        f"the proving run was not shown to be configured: {absent}. A run whose "
        "rootdir is a tempdir loads neither pyproject.toml nor the shipped "
        "conftest, so it measures an unconfigured pipeline and proves nothing "
        "(the recorded CS-855 residual). The third fact is behavioural: "
        "xfail_strict turns a passing xfail into a failure, which no "
        "unconfigured run can produce"
    )


@pytest.mark.parametrize("arm", ["guarded", "control"])
def test_both_arms_detected_rather_than_crashed(arm, guarded_run, control_run):
    run = guarded_run if arm == "guarded" else control_run
    assert "INTERNALERROR" not in run.output, f"the {run.label} sandbox crashed pytest itself"
    assert run.returncode == PYTEST_TESTS_FAILED, (
        f"the {run.label} sandbox exited {run.returncode} rather than "
        f"{PYTEST_TESTS_FAILED}. A sandbox that died during collection renders "
        "no personal data either, and that is not the property under test"
    )
    collected = f"collected {EXPECTED_FAILURES} items" in run.output
    assert collected, f"the {run.label} sandbox did not collect {EXPECTED_FAILURES} tests"
    assert f"{EXPECTED_FAILURES} failed" in run.output, (
        f"the {run.label} sandbox did not report {EXPECTED_FAILURES} failures"
    )
    rendered = sorted(failure_blocks(run.output))
    missing = sorted(name for name in EXPECTED_BLOCKS if name not in rendered)
    assert missing == [], f"the {run.label} sandbox rendered no block for {missing}"


def test_the_control_arm_carries_every_class_in_every_mechanism_block(control_run):
    _assert_home_oracle_is_not_vacuous()
    blocks = failure_blocks(control_run.output)
    needles = _class_needles()
    barren: list[str] = []
    for mechanism in MECHANISM_TESTS:
        text = blocks.get(mechanism, "")
        for class_id, spellings in needles.items():
            if not _surviving_labels(text, spellings):
                barren.append(f"{mechanism}/{class_id}")
    assert barren == [], (
        "the UNGUARDED twin does not render this class in this mechanism's "
        f"block: {sorted(barren)}. For a COVERED class that makes the matching "
        "guarded arm look for nothing, so a green result from it would be "
        "vacuous. For an UNCOVERED class it is what makes the declared gap a "
        "MEASURED fact - the needle demonstrably reaches a rendered report - "
        "rather than an assertion about a value nothing prints"
    )


def test_the_guarded_report_is_redacted_rather_than_deleted(guarded_run):
    region = guarded_region(guarded_run.output)
    gone = sorted(fragment for fragment in SURVIVING_FRAGMENTS if fragment not in region)
    assert gone == [], (
        "the guarded report lost text that carries no personal data at all: "
        f"{gone}. A remedy that blanks a report passes every leak scan in this "
        "module and is useless, so what must SURVIVE is asserted too"
    )
    blocks = sorted(failure_blocks(guarded_run.output))
    missing = sorted(name for name in EXPECTED_BLOCKS if name not in blocks)
    assert missing == [], f"the guarded report lost whole failure blocks: {missing}"


# ---------------------------------------------------------------------------
# One arm per class. Each asserts BOTH halves: nothing of that class survives,
# and that class's placeholder is present. The second half is what kills a
# mutant on a machine where deleting one class's rules leaves another class's
# rule covering the same characters.
# ---------------------------------------------------------------------------


def _assert_class_is_redacted(run: SandboxRun, class_id: str) -> None:
    """Grade one class over the whole guarded region and per mechanism block."""
    region = guarded_region(run.output)
    spellings = _class_needles()[class_id]
    leaked = _surviving_labels(region, spellings)
    assert leaked == [], (
        f"the {class_id} class survived the shipped redaction under the "
        f"configured pipeline. Spellings still rendered: {leaked}. No value is "
        "printed here - the labels are the finding"
    )
    # Bound to a scalar: ``region`` is a whole rendered report, and under a
    # mutant that hollows the rules it is an UNREDACTED one.
    fingerprint = CLASS_FINGERPRINTS[class_id]
    fingerprint_present = fingerprint in region
    assert fingerprint_present, (
        f"no {class_id} placeholder appears anywhere in the guarded report, so "
        "that class's rules did not run. A leak scan alone cannot see this: on "
        "a machine whose account name is the only personal component of its "
        "home prefix, deleting the home rules leaves nothing for a scan to find"
    )
    blocks = failure_blocks(run.output)
    per_block = sorted(
        f"{mechanism}: {_surviving_labels(blocks.get(mechanism, ''), spellings)}"
        for mechanism in MECHANISM_TESTS
        if _surviving_labels(blocks.get(mechanism, ""), spellings)
    )
    assert per_block == [], f"the {class_id} class survived in a mechanism block: {per_block}"


def test_the_home_path_class_is_redacted_on_every_mechanism(guarded_run):
    _assert_home_oracle_is_not_vacuous()
    _assert_class_is_redacted(guarded_run, shipped.CLASS_HOME_PATH)


def test_the_home_path_doubled_spelling_is_the_channel_a_chained_cause_renders(guarded_run):
    # THE ARM THAT MUST SKIP LOUDLY RATHER THAN PASS QUIETLY. On a platform with
    # no backslashes the doubled spelling IS the native one, so the gap this
    # item exists for cannot be reproduced and a green result here would be a
    # statement about nothing.
    home = str(Path.home())
    if BACKSLASH not in home:
        pytest.skip(
            "this platform spells no path separator as a backslash, so the "
            "%r-DOUBLED home spelling - the channel OSError.__str__ renders "
            "and the one CS-860 was opened for - cannot exist here. The "
            "doubling gap is UNMEASURED on this platform, not absent"
        )
    doubled = home.replace(BACKSLASH, BACKSLASH * 2)
    # BOUND TO A SCALAR BEFORE THE ASSERT, AND THAT IS NOT STYLE. pytest renders
    # the asserted EXPRESSION independently of the message, so asserting over
    # the redacted string itself prints a value derived from the real home into
    # the failure report - MEASURED: with both rule families hollowed, this
    # shape carried the bare account name verbatim. Its leak-safety would then
    # depend on the very rules under test, which is circular.
    reached_home_rule = REDACTED_HOME in redact_personal_data(doubled)
    assert reached_home_rule, (
        "the doubled home spelling did not reach the HOME rule. Before CS-860 "
        "it was caught only by the account-name rule, which holds on this "
        "machine by naming accident and does not transfer to another"
    )
    block = failure_blocks(guarded_run.output).get(CHAINED_CAUSE_TEST, "")
    leaked = _surviving_labels(block, {"home-doubled": doubled})
    assert leaked == [], f"the doubled spelling survived the chained cause: {leaked}"


def test_the_account_name_class_is_redacted_on_every_mechanism(guarded_run):
    _assert_class_is_redacted(guarded_run, shipped.CLASS_ACCOUNT_NAME)


def _assert_registered_uncovered(class_id: str) -> None:
    """Grade one UNCOVERED class: declared, reasoned, unserved and unreached."""
    assert class_id in UNCOVERED_CLASSES, (
        f"{class_id} is graded here as an uncovered class and is not declared "
        "one. If it has become covered, this arm is the wrong shape for it"
    )
    assert class_id not in COVERED_CLASSES, f"{class_id} is declared both covered and uncovered"
    reason = UNCOVERED_CLASSES[class_id]
    words = len(reason.split())
    assert words >= MIN_REASON_WORDS, (
        f"the {class_id} exemption states {words} words of reason, below the "
        f"{MIN_REASON_WORDS} this suite accepts. A registered exemption with no "
        "usable reason is the silence the registry exists to prevent, wearing "
        "the registry's clothes"
    )
    assert class_id not in _served_classes(), (
        f"a rule is tagged {class_id} while the class is declared UNCOVERED"
    )
    assert class_id not in CLASS_FINGERPRINTS, (
        f"{class_id} is uncovered and carries a placeholder fingerprint anyway"
    )
    for label, probe in sorted(_class_needles()[class_id].items()):
        assert redact_personal_data(probe) == probe, (
            f"the {class_id} probe {label} was rewritten by the shipped rule set "
            "while its class is declared UNCOVERED. The declaration and the "
            "behaviour disagree - either a rule has come back, in which case the "
            "class belongs in COVERED_CLASSES where the behavioural arm can "
            "grade it, or something else is over-reaching onto this shape"
        )


def test_the_account_id_class_is_registered_uncovered_with_a_stated_reason():
    # REGISTERED, NOT DROPPED. CS-860's positional rule was backed out; the
    # class stays declared so the gap is machine-checked. This arm is what
    # converts "we removed it" into a standing fact the next edit has to face.
    _assert_registered_uncovered(shipped.CLASS_ACCOUNT_ID)
    positional = SAVE_ROOT_MARKER + "/" + PLANTED_ACCOUNT_ID
    assert redact_personal_data(positional) == positional, (
        "an account directory below the save root was redacted while the "
        "account-id class is declared UNCOVERED. THE GAP IS DECLARED RATHER "
        "THAN HIDDEN: if a positional rule has been rebuilt on a mechanism that "
        "does not assume its input is a path, move the class to COVERED_CLASSES "
        "and this arm becomes the wrong shape for it"
    )
    bare = redact_personal_data(PLANTED_ACCOUNT_ID)
    assert bare == PLANTED_ACCOUNT_ID, (
        "a bare digit run outside any save path was rewritten. That is the "
        "free-floating digit rule this project has rejected twice: it would "
        "rewrite the synthetic account tokens the leak detectors own"
    )


def test_the_world_name_class_is_registered_uncovered_with_a_stated_reason():
    # REGISTERED, NOT DROPPED, for the same reason as the account id above.
    _assert_registered_uncovered(shipped.CLASS_WORLD_NAME)
    bare = PLANTED_SAVE_STEM
    assert redact_personal_data(bare) == bare, (
        "a bare save-derived name was rewritten. It is free text derivable from "
        "nothing on this machine, so no rule can legitimately recognise one; "
        "the boundary record in tests/test_assertion_rendering.py depends on it"
    )
    unrelated = "notes.savings"
    assert redact_personal_data(unrelated) == unrelated, (
        "a longer word merely beginning with the suffix was cut in half"
    )


def test_a_redaction_never_erases_the_frame_around_a_save_filename():
    # THE TOO-GREEDY COUNTER-EXAMPLE, PINNED. The backed-out rule's segment
    # class admitted brackets, commas and colons and was unanchored, so on a
    # real traceback frame line it consumed the function name as well:
    # `workdir.py:120: in copy_for_read(World.sav)` rendered as
    # `workdir.py:120: in <redacted-save>)`. THIS ARM SURVIVES A CORRECT
    # REBUILD - a rule may redact the filename here, it may never eat the frame
    # around it - so it is a standing guard rather than a record of a removal.
    frame = "workdir.py:120: in copy_for_read(World.sav)"
    redacted = redact_personal_data(frame)
    assert "copy_for_read" in redacted, (
        "a redaction erased a FUNCTION NAME from a traceback frame line, which "
        "is undiagnosable rather than merely lossy. A path-segment character "
        "class is correct on a PATH and destructive on the arbitrary prose a "
        f"failure report is - see tests/conftest.py's docstring. Rendered: {redacted!r}"
    )
    delimited = "(Alpha.sav,Bravo.sav,Charlie.sav)"
    out = redact_personal_data(delimited)
    assert out.count(",") == delimited.count(","), (
        "a redaction swallowed across the commas of a bracketed list, so three "
        f"items collapsed into one. Rendered: {out!r}"
    )
    assert out.endswith(")"), (
        "a redaction consumed the closing bracket of a list, so the frame no "
        f"longer parses as one. Rendered: {out!r}"
    )


def test_a_redaction_never_leaves_half_a_spaced_save_filename():
    # THE TOO-NARROW COUNTER-EXAMPLE, PINNED, AND IT IS THE HALF THAT LEAKED.
    # The same segment class excluded whitespace, so the rule ate only the run
    # after the last space: `Some Save Name.sav` rendered as
    # `Some Save <redacted-save>` and the world name walked out in the part left
    # behind. THIS ARM ALSO SURVIVES A CORRECT REBUILD: a rule that takes the
    # whole name removes the first token too, and a rule that takes nothing
    # leaves the string alone. Only the partial rewrite fails it.
    spaced = "Some Save Name.sav"
    out = redact_personal_data(spaced)
    partial = out != spaced and "Some" in out
    assert not partial, (
        "a redaction rewrote PART of a spaced save filename and left the rest "
        "standing, which leaks the world name it exists to hide while reading "
        f"as redacted. Rendered: {out!r}"
    )
    quoted = "Bob's World.sav"
    out_quoted = redact_personal_data(quoted)
    partial_quoted = out_quoted != quoted and "Bob" in out_quoted
    assert not partial_quoted, (
        f"the same partial rewrite on an apostrophe rather than a space: {out_quoted!r}"
    )
