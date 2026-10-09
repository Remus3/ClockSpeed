#!/usr/bin/env python3
"""The third-party register, graded against what this tree actually vendors.

``THIRD_PARTY.md`` is the OWNER of the fact "what is vendored here and under
what licence" (``CLAUDE.md`` section 4). An owner file that denies the thing it
owns is worse than no owner at all, because every other file is instructed to
link to it rather than restate it - so the denial is the answer a reader gets.

THE DEFECT THIS MODULE WAS WRITTEN AGAINST, measured before the repair: the
register's Current state section asserted that zero files in this repository
were copied, adapted or derived from an external codebase, and its table
carried a ``(none vendored)`` placeholder row. ``docs/CHANNEL.md`` had been
vendored byte-identical from another repository under Apache-2.0 five days
earlier, recorded in ``docs/LEDGER.md`` under CS-1095 and attributed in
``CLAUDE.md``'s section 4 topology row - which is the WRONG owner for a licence
verdict. Both register claims were false, and a register nothing grades drifts
the day after it is written.

THE SECOND DEFECT, MEASURED 2026-09-20 AND THE REASON THE ROSTER IS NOW
DERIVED: the module's first cut named its byte-pin modules in a hand-written
``BYTE_PIN_ROSTER`` dict. That is an allowlist wearing a guard's clothes - it
can only ever grade the files somebody remembered to add, which is the
complement of the failure case. ``ops/loop/slots.py`` was vendored
byte-identical from the same lane the loop came from, and no arm here moved,
because nobody had added its row to the roster. :func:`_byte_pinned_paths` now
DISCOVERS the population instead: it walks every test module under ``tests/``,
and for each one that spells a sha256 literal it asks whether any repo-relative
``Path`` the module binds actually hashes to one of them. The oracle is the
BYTES, not a name anybody maintains, so a vendored file arrives in the graded
population the moment its pin does.

THE DEFAULT IS THEREFORE RED, WHICH IS THE WHOLE POINT. A byte-pinned file that
is neither listed in the register nor declared in
:data:`PINNED_BUT_AUTHORED_HERE` fails :func:`test_every_byte_pinned_file_is_registered`.
Escaping the register takes a written declaration with a reason, rather than
the silence that let the second defect through.

WHAT THE DERIVATION STILL DOES NOT COVER, stated rather than left to be
discovered: a lift that arrives with NO byte pin at all and no register row is
invisible here, because this module's whole oracle is the pin.
:func:`test_every_registered_vendored_file_is_byte_pinned` closes that hole in
one direction only - it forces a pin for anything the register DOES name. The
residual class - a file lifted into this tree that nobody pinned and nobody
registered - is CS-1165, and this module makes no claim about it.

THE PHRASE ARM IS A BACKSTOP, NOT THE GUARD. :data:`DENIAL_PATTERNS` is a closed
vocabulary of blanket denials, so a future denial worded outside it escapes.
:func:`test_the_denial_vocabulary_is_not_vacuous` exists because a regex that
matches nothing passes this kind of arm for exactly the wrong reason - it fires
each pattern at a string built to trip it, so the arm cannot be green because
the vocabulary is broken.

THE ATTRIBUTION CELLS ARE PINNED AS CONTENT, transcribed from ``CLAUDE.md``
section 4's topology row, the CS-1095 licence-gate entry in ``docs/LEDGER.md``
and the CS-946 gate entry for the loop files - the places the facts were
recorded before this file owned them. They are pinned HERE rather than read from
those files at runtime because the whole point of the repair is that the
register becomes the owner: an arm that read the attribution back out of
``CLAUDE.md`` would make the register's correctness depend on a row the merger
may legitimately reduce to a pointer.
"""

from __future__ import annotations

import hashlib
import importlib
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The register itself.
REGISTER = REPO_ROOT / "THIRD_PARTY.md"

#: The tree discovery walks. Only this repository's own suite is read - a
#: sibling tree's pin is green-by-skip on any machine that lacks it.
TESTS_DIR = REPO_ROOT / "tests"

#: The heading that opens the machine-graded table of vendored files. The
#: register's other table records items merely CONSIDERED, which name no file
#: and must not be swept into a path-resolution arm.
VENDORED_HEADING = "### Vendored files"

#: A sha256 spelled out, which is how every byte pin in this tree writes one.
DIGEST_RE = re.compile(r"\b[0-9a-f]{64}\b")

#: Repo-relative paths this tree byte-pins that are NOT vendorings, each mapped
#: to the reason it is exempt. A file reaches this map by somebody writing a
#: sentence about it; the ABSENCE of an entry is red, not silent, which is the
#: inversion the hand-maintained roster got backwards. Empty today.
PINNED_BUT_AUTHORED_HERE: dict[str, str] = {}

#: An anti-vacuity FLOOR for discovery, and deliberately not a roster: nothing
#: in this tuple can make the register arms pass for a file that is missing
#: from the register, because those arms read the DISCOVERED set. It exists
#: because discovery that silently narrowed - a renamed digest style, a pin
#: module that stopped binding its Path - would make every arm below agree
#: about a smaller population and report green for it.
DISCOVERY_FLOOR = (
    "docs/CHANNEL.md",
    "ops/loop/slots.py",
    "ops/loop/winmutex.py",
    # CS-1231 - the fleet kit, first vendored at version 4; CS-1272 re-vendored
    # it at version 9, CS-1282 at version 10 and CS-1287 at version 11, all
    # seventeen files pinned by tests/test_fleet_kit.py.
    "ops/fleet_kit/FLEET-COMMON.md",
    "ops/fleet_kit/LICENSE",
    "ops/fleet_kit/MANIFEST.json",
    "ops/fleet_kit/NOTICE",
    "ops/fleet_kit/fleet_headless.py",
    "ops/fleet_kit/cli_display.json",
    "ops/fleet_kit/fleet_checklist.py",
    "ops/fleet_kit/fleet_done.py",
    "ops/fleet_kit/fleet_inbox.py",
    "ops/fleet_kit/fleet_lanes.py",
    "ops/fleet_kit/fleet_secrets.py",
    "ops/fleet_kit/fleet_statusline.js",
    "ops/fleet_kit/fleet_subagent_first.py",
    "ops/fleet_kit/fleet_subagent_status.js",
    "ops/fleet_kit/fleet_watch.py",
    "ops/fleet_kit/tokens.css",
    "ops/fleet_kit/tokens.json",
)

#: A backticked token, which is how every path in this tree's docs is spelled.
BACKTICK_RE = re.compile(r"`([^`\n]+)`")

#: Blanket denials of vendoring. Matched against WHITESPACE-NORMALISED text,
#: because the register wraps its prose and the original false sentence spanned
#: two lines - a line-anchored search would have missed the defect this module
#: was written against. The one-file wording is here because it was the SECOND
#: false sentence: true when it was written, false the day a second file landed.
DENIAL_PATTERNS = (
    re.compile(r"no third-party source is vendored", re.IGNORECASE),
    re.compile(r"zero files in this repository were copied", re.IGNORECASE),
    re.compile(r"\(none vendored\)", re.IGNORECASE),
    re.compile(r"nothing in this repository is vendored", re.IGNORECASE),
    re.compile(r"nothing is vendored", re.IGNORECASE),
    re.compile(r"exactly one file in this repository is vendored", re.IGNORECASE),
)

#: Text built to trip every pattern above, so the vocabulary cannot rot silently.
DENIAL_PROBE = (
    "No third-party source is vendored in this project. Zero files in this "
    "repository were copied, adapted or derived from an external codebase. "
    "| (none vendored) | - | Nothing in this repository is vendored. "
    "Nothing is vendored. Exactly one file in this repository is vendored."
)

#: Cells a vendored row must carry, per file, transcribed from the licence-gate
#: entries in ``docs/LEDGER.md``. Each is a fact a garbled re-pin would lose:
#: the grant, the holder, the upstream repository, the gate record and the
#: module that holds the bytes to the pin. A row may carry more; it may not
#: carry less.
ROW_FACTS: dict[str, tuple[str, ...]] = {
    "docs/CHANNEL.md": (
        "Apache-2.0",
        "`Moonbeam`",
        "`Remus3/Amberstone`",
        "CS-1095",
        "`tests/test_channel_doc.py`",
    ),
    "ops/loop/slots.py": (
        "Apache-2.0",
        "`Moonbeam`",
        "`Remus3/Legion-Wallpaper`",
        "CS-946",
        "`tests/ops/test_shared_slots.py`",
    ),
    "ops/loop/winmutex.py": (
        "Apache-2.0",
        "`Moonbeam`",
        "`Remus3/Legion-Wallpaper`",
        "ADR-0017",
        "`tests/test_lane_lock.py`",
    ),
    # CS-1231 - the fleet kit, gated CLEARED before the lift. The holder is
    # recorded AS READ in the kit's NOTICE - a role, never a name inferred from
    # elsewhere - and the kit has no public upstream repository to cite. Two rows
    # quote NOTICE's whole holder line, so their fact is that line verbatim.
    # CS-1272 re-vendored all five at version 9, CS-1282 at version 10 and
    # CS-1287 at version 11, so each row now names all four items.
    "ops/fleet_kit/fleet_headless.py": (
        "Apache-2.0",
        "`the operator - the kit's owner and sole copyright holder`",
        "CS-1231",
        "CS-1272",
        "CS-1282",
        "CS-1287",
        "`tests/test_fleet_kit.py`",
    ),
    "ops/fleet_kit/FLEET-COMMON.md": (
        "Apache-2.0",
        "`the operator`",
        "CS-1231",
        "CS-1272",
        "CS-1282",
        "CS-1287",
        "`tests/test_fleet_kit.py`",
    ),
    "ops/fleet_kit/MANIFEST.json": (
        "Apache-2.0",
        "`the operator`",
        "CS-1231",
        "CS-1272",
        "CS-1282",
        "CS-1287",
        "`tests/test_fleet_kit.py`",
    ),
    "ops/fleet_kit/LICENSE": (
        "Apache-2.0",
        "`the operator`",
        "CS-1231",
        "CS-1272",
        "CS-1282",
        "CS-1287",
        "`tests/test_fleet_kit.py`",
    ),
    "ops/fleet_kit/NOTICE": (
        "Apache-2.0",
        "`the operator - the kit's owner and sole copyright holder`",
        "CS-1231",
        "CS-1272",
        "CS-1282",
        "CS-1287",
        "`tests/test_fleet_kit.py`",
    ),
    # CS-1272 - the eleven files version 9 added, re-read at version 10 under
    # CS-1282 and at version 11 under CS-1287. Two facts beyond the grant,
    # holder, item and pin are stated where they hold, because a reader of the
    # bytes alone would get them wrong: the three data files carry NO SPDX
    # header (JSON cannot, and tokens.css is generated without one), and
    # NOTICE's governing clause - quoted verbatim -
    # covers every file MANIFEST.json names, which at version 9 was the ONLY
    # route for the seven files its scope list omitted. Version 10's list names
    # them all; the rows keep the clause, the grant that reaches a later file too.
    "ops/fleet_kit/cli_display.json": (
        "Apache-2.0",
        "`the operator`",
        "CS-1272",
        "CS-1282",
        "CS-1287",
        "`tests/test_fleet_kit.py`",
        "no SPDX header",
        "`every file named in this kit's MANIFEST.json`",
    ),
    "ops/fleet_kit/fleet_checklist.py": (
        "Apache-2.0",
        "`the operator - the kit's owner and sole copyright holder`",
        "CS-1272",
        "CS-1282",
        "CS-1287",
        "`tests/test_fleet_kit.py`",
        "`every file named in this kit's MANIFEST.json`",
    ),
    "ops/fleet_kit/fleet_done.py": (
        "Apache-2.0",
        "`the operator - the kit's owner and sole copyright holder`",
        "CS-1272",
        "CS-1282",
        "CS-1287",
        "`tests/test_fleet_kit.py`",
        "`every file named in this kit's MANIFEST.json`",
    ),
    "ops/fleet_kit/fleet_inbox.py": (
        "Apache-2.0",
        "`the operator - the kit's owner and sole copyright holder`",
        "CS-1272",
        "CS-1282",
        "CS-1287",
        "`tests/test_fleet_kit.py`",
        "`every file named in this kit's MANIFEST.json`",
    ),
    "ops/fleet_kit/fleet_lanes.py": (
        "Apache-2.0",
        "`the operator - the kit's owner and sole copyright holder`",
        "CS-1272",
        "CS-1282",
        "CS-1287",
        "`tests/test_fleet_kit.py`",
        "`every file named in this kit's MANIFEST.json`",
    ),
    "ops/fleet_kit/fleet_secrets.py": (
        "Apache-2.0",
        "`the operator - the kit's owner and sole copyright holder`",
        "CS-1272",
        "CS-1282",
        "CS-1287",
        "`tests/test_fleet_kit.py`",
    ),
    "ops/fleet_kit/fleet_statusline.js": (
        "Apache-2.0",
        "`the operator - the kit's owner and sole copyright holder`",
        "CS-1272",
        "CS-1282",
        "CS-1287",
        "`tests/test_fleet_kit.py`",
        "`every file named in this kit's MANIFEST.json`",
    ),
    # CS-1282 - the one file version 10 added: the SUBAGENT-FIRST hook; re-read
    # at version 11 under CS-1287.
    "ops/fleet_kit/fleet_subagent_first.py": (
        "Apache-2.0",
        "`the operator - the kit's owner and sole copyright holder`",
        "CS-1282",
        "CS-1287",
        "`tests/test_fleet_kit.py`",
        "`every file named in this kit's MANIFEST.json`",
    ),
    "ops/fleet_kit/fleet_subagent_status.js": (
        "Apache-2.0",
        "`the operator - the kit's owner and sole copyright holder`",
        "CS-1272",
        "CS-1282",
        "CS-1287",
        "`tests/test_fleet_kit.py`",
        "`every file named in this kit's MANIFEST.json`",
    ),
    "ops/fleet_kit/fleet_watch.py": (
        "Apache-2.0",
        "`the operator - the kit's owner and sole copyright holder`",
        "CS-1272",
        "CS-1282",
        "CS-1287",
        "`tests/test_fleet_kit.py`",
    ),
    "ops/fleet_kit/tokens.css": (
        "Apache-2.0",
        "`the operator`",
        "CS-1272",
        "CS-1282",
        "CS-1287",
        "`tests/test_fleet_kit.py`",
        "no SPDX header",
    ),
    "ops/fleet_kit/tokens.json": (
        "Apache-2.0",
        "`the operator`",
        "CS-1272",
        "CS-1282",
        "CS-1287",
        "`tests/test_fleet_kit.py`",
        "no SPDX header",
    ),
}

#: Seconds allowed for the one child this module spawns. An unbounded child
#: cannot fail the arm that owns it; it burns the job budget instead.
GIT_TIMEOUT = 30

#: The rows a markdown table spends before its body: the header and the
#: separator under it. Named rather than spelled twice, so the slice below and
#: the assertion above it cannot drift.
TABLE_PREAMBLE_ROWS = 2


def _register_text() -> str:
    """Return the register decoded as ASCII with newlines normalised to LF.

    Returns:
        The document text.
    """
    return REGISTER.read_bytes().decode("ascii").replace("\r\n", "\n")


def _flat(text: str) -> str:
    """Return ``text`` with every run of whitespace collapsed to one space.

    Args:
        text: Any document text.

    Returns:
        The single-spaced form, which is what a wrapped sentence must be
        matched against.
    """
    return re.sub(r"\s+", " ", text)


def _table_rows(text: str, heading: str) -> list[list[str]]:
    """Return the body rows of the first markdown table under ``heading``.

    Args:
        text: The whole document.
        heading: The exact heading line that opens the table's section.

    Returns:
        One list of stripped cells per body row, header and separator dropped.

    Raises:
        AssertionError: If the heading is absent or no table follows it.
    """
    assert heading in text, f"{REGISTER.name} carries no {heading!r} section"
    section = text.split(heading, 1)[1]
    rows: list[list[str]] = []
    for line in section.splitlines():
        if line.startswith("|"):
            rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
        elif rows:
            break
    assert len(rows) >= TABLE_PREAMBLE_ROWS, (
        f"the table under {heading!r} has no header and separator"
    )
    return rows[TABLE_PREAMBLE_ROWS:]


def _listed_paths(text: str) -> list[str]:
    """Return the repo-relative path each vendored row names, in file order.

    Args:
        text: The whole document.

    Returns:
        The backticked token from column 0 of every vendored-files row.

    Raises:
        AssertionError: If a row's first cell carries no backticked token.
    """
    listed: list[str] = []
    for row in _table_rows(text, VENDORED_HEADING):
        quoted = BACKTICK_RE.findall(row[0])
        assert quoted, f"a vendored row names no backticked file: {row[0]!r}"
        listed.append(quoted[0])
    return listed


def _module_name(source: Path) -> str:
    """Return the dotted import name of a test module inside this tree.

    Args:
        source: The module's path on disk.

    Returns:
        The dotted name, e.g. ``tests.ops.test_shared_slots``.
    """
    return ".".join(source.resolve().relative_to(REPO_ROOT).with_suffix("").parts)


def _digests_of(raw: bytes) -> set[str]:
    """Return the sha256 of ``raw`` both as-is and LF-normalised.

    Both forms are computed because this tree's pins disagree about which one
    they take: the channel doc pins the LF-normalised bytes so a checkout that
    materialised CRLF still hashes equal, and the loop files pin the bytes on
    disk. A discovery that knew only one shape would miss half the population.

    Args:
        raw: A file's bytes.

    Returns:
        The one or two hex digests those bytes can be pinned at.
    """
    return {
        hashlib.sha256(raw).hexdigest(),
        hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest(),
    }


def _byte_pinned_paths() -> dict[str, str]:
    """Return every repo file whose bytes a test module pins, and what pins it.

    DISCOVERED, NOT ROSTERED. Each test module is scanned for sha256 literals;
    a module that spells none cannot be a byte pin and is not imported. A
    module that spells one is imported and every module-level ``Path`` it binds
    is hashed, so the link between a pin and the file it pins is established by
    the BYTES agreeing rather than by a name a human kept in step.

    Returns:
        Repo-relative POSIX paths mapped to the ``module.ATTRIBUTE`` that pins
        them, one entry per file.
    """
    pinned: dict[str, str] = {}
    for source in sorted(TESTS_DIR.rglob("test_*.py")):
        digests = set(DIGEST_RE.findall(source.read_bytes().decode("utf-8", "replace")))
        if not digests:
            continue
        module = importlib.import_module(_module_name(source))
        for attribute in sorted(vars(module)):
            value = vars(module)[attribute]
            if not isinstance(value, Path) or not value.is_file():
                continue
            resolved = value.resolve()
            if REPO_ROOT not in resolved.parents:
                continue
            if _digests_of(resolved.read_bytes()) & digests:
                relative = resolved.relative_to(REPO_ROOT).as_posix()
                pinned.setdefault(relative, f"{module.__name__}.{attribute}")
    return pinned


def test_the_vendored_files_table_parses_and_names_at_least_one_file() -> None:
    # Anti-vacuity for every arm below: each of them reads this table, and a
    # table that had stopped parsing would make all of them agree about nothing.
    listed = _listed_paths(_register_text())
    assert listed, (
        "the register's vendored-files table has no rows, so every arm that "
        "reads it is measuring an empty population"
    )


def test_byte_pin_discovery_still_reaches_the_files_it_is_known_to_reach() -> None:
    # Anti-vacuity for discovery itself. This does NOT decide what must be
    # registered - the arms below read the discovered set, never this floor -
    # it only refuses a discovery that has quietly stopped finding things.
    pinned = _byte_pinned_paths()
    lost = sorted(path for path in DISCOVERY_FLOOR if path not in pinned)
    assert lost == [], (
        f"byte-pin discovery no longer reaches {lost}, which it reached when "
        f"this floor was measured. It found {sorted(pinned)}. A narrowed "
        "discovery makes every arm below green over a smaller population."
    )


def test_every_byte_pinned_file_is_registered() -> None:
    # THE ARM THE MODULE EXISTS FOR, and its oracle is the pinned BYTES rather
    # than any list of files - so a vendoring nobody remembered to register is
    # red here the moment its pin lands, which is the defect that produced it.
    pinned = _byte_pinned_paths()
    assert pinned, "byte-pin discovery found nothing, so this arm graded nothing"
    listed = _listed_paths(_register_text())
    missing = sorted(
        f"{path} (pinned by {pin})"
        for path, pin in pinned.items()
        if path not in listed and path not in PINNED_BUT_AUTHORED_HERE
    )
    assert missing == [], (
        "a file this tree byte-pins is absent from the third-party register: "
        f"{missing}. The register is the owner of what is vendored and under "
        "what licence; a vendored file it does not name is a licence obligation "
        "recorded nowhere. If the file is authored HERE and merely pinned, say "
        "so in PINNED_BUT_AUTHORED_HERE with a reason."
    )


def test_every_registered_vendored_file_is_byte_pinned() -> None:
    # The other direction over the same two populations. A vendored file with
    # no pin can be edited here without anything noticing, and then the row
    # above it describes bytes this tree has silently made its own.
    listed = _listed_paths(_register_text())
    pinned = _byte_pinned_paths()
    unpinned = sorted(path for path in listed if path not in pinned)
    assert unpinned == [], (
        f"the register lists {unpinned} as vendored, and no test module pins "
        "those bytes. A vendored file nothing pins drifts from its upstream "
        "silently, and the row's licence verdict then describes a file that no "
        "longer exists here."
    )


def test_the_authored_here_declarations_are_real_and_reasoned() -> None:
    # An escape hatch nothing grades is a hole. Every declared exemption must
    # name a file discovery actually found, and must carry a reason.
    pinned = _byte_pinned_paths()
    broken = sorted(
        path
        for path, reason in PINNED_BUT_AUTHORED_HERE.items()
        if path not in pinned or not reason.strip()
    )
    assert broken == [], (
        f"these register exemptions name no byte-pinned file, or carry no "
        f"reason: {broken}. A stale exemption silently excuses whatever path "
        "later takes that name."
    )


def test_the_register_makes_no_blanket_denial_while_a_file_is_vendored() -> None:
    # The backstop arm. It is conditional on there BEING a vendored file, so a
    # tree that genuinely vendors nothing is free to say so.
    pinned = _byte_pinned_paths()
    assert pinned, "byte-pin discovery found nothing, so this arm graded nothing"
    flat = _flat(_register_text())
    denials = [pattern.pattern for pattern in DENIAL_PATTERNS if pattern.search(flat)]
    assert denials == [], (
        f"the register denies that anything is vendored, or undercounts what "
        f"is - {denials} - while {sorted(pinned)} are vendored and byte-pinned. "
        "The owner file's answer is the answer every other file points at."
    )


def test_the_denial_vocabulary_is_not_vacuous() -> None:
    # A regex that matches nothing passes the arm above for the wrong reason.
    silent = [
        pattern.pattern for pattern in DENIAL_PATTERNS if not pattern.search(_flat(DENIAL_PROBE))
    ]
    assert silent == [], (
        f"these denial patterns match nothing even in the probe built to trip "
        f"them: {silent}. The arm that uses them would be green by construction."
    )


def test_every_file_the_register_lists_is_present_and_tracked() -> None:
    # A register that lists a file the tree no longer carries is as wrong as
    # one that omits a file the tree does carry - and "on disk" is not enough
    # here, because an untracked file is not something this repository
    # distributes and so carries no redistribution obligation.
    listed = _listed_paths(_register_text())
    absent = sorted(path for path in listed if not (REPO_ROOT / path).is_file())
    assert absent == [], f"the register lists a vendored file that is not in the tree: {absent}"

    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", *listed],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
        timeout=GIT_TIMEOUT,
    )
    assert tracked.returncode == 0, (
        "the register lists a vendored file git does not track, so the licence "
        f"obligation it records attaches to nothing this repository ships: "
        f"{tracked.stderr.decode('ascii', 'replace').strip()}"
    )


def test_each_vendored_row_carries_its_upstream_and_its_grant() -> None:
    # Apache-2.0 section 4 asks a redistributor to retain the attribution. The
    # vendored bytes may not be edited to carry a notice - two of the three are
    # byte-identical-by-contract with sibling trees and the third is a declared
    # fork - so the attribution lives in the row, which makes the row's CONTENT
    # the obligation rather than its presence. A shape-only arm would pass on a
    # blanked row.
    rows = _table_rows(_register_text(), VENDORED_HEADING)
    faults: list[str] = []
    for path, facts in ROW_FACTS.items():
        matching = [row for row in rows if path in row[0]]
        if len(matching) != 1:
            faults.append(f"{path}: {len(matching)} rows, not exactly one")
            continue
        cells = " | ".join(matching[0])
        missing = [fact for fact in facts if fact not in cells]
        if missing:
            faults.append(f"{path}: lost {missing}")
    assert faults == [], (
        f"a vendored row has lost part of its Apache-2.0 attribution: {faults}. "
        "The pinned files cannot carry a notice of their own, so these rows ARE "
        "the retained attribution."
    )
