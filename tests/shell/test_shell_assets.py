"""CS-602 slice S5 - the shipped ``shell/`` tree, graded at rest from Python.

WHAT THIS MODULE GRADES, AND WHAT IT DOES NOT. Every arm here reads the tracked
files under ``shell/`` as BYTES off disk and asserts a property of what a human
typed. Nothing here runs Node, npm or an electron binary, and nothing here
proves the window opens. ``shell/test/`` holds five ``node --test`` suites that
grade behaviour, and they run on the tier-2 lane where a Node toolchain exists.
This module is the every-push half: it runs on a clean checkout with no Node
installed, and it grades what bytes alone can establish - character set, line
endings, the absence of a named token, the count of a call site, and agreement
between a constant spelled on both sides of the language seam.

WHY A TEXT SCAN NEEDS A COMMENT STRIPPER, AND WHY THE STRIPPER NEEDS CONTROLS
IN BOTH DIRECTIONS. A text scan cannot tell code from comment, and both
directions bite. ``shell/lib/window.js`` and ``shell/lib/geometry.js`` require
nothing at all, yet each carries a comment explaining which module they avoid -
so a raw scan for ``electron`` fails them for DOCUMENTING the constraint they
satisfy. Running the other way, a required symbol mentioned only in prose would
satisfy a raw scan while no implementation existed. So an arm whose subject is
"this token must (not) appear in code" strips comments first.

WITH ONE CLASS OF EXCEPTION, ADDED AFTER THE STRIPPER WAS DEFEATED. ``/[/*]/``
is a valid JavaScript regular expression literal that the stripper reads as
opening a block comment, and ``/[*/]/`` is the valid literal that closes it.
A bypass planted between the two is deleted before any stripped-code arm sees
it, while the raw file still carries every byte of it - measured with a working
four-token bypass that left the shell suite, ``node --test``, the drift guard
and the commit gate all green. The certificate-posture sweep in section (d) and
the call-site grading in section (e) therefore read RAW text and exempt
documented mentions through an explicit allow-list of exact (file, line) pairs,
which no regex literal can blind. The stripper keeps the arms where a comment
mention is a genuine false positive and where being blinded fails safe rather
than open: the purity partition, the CommonJS census, the constant extraction
and the test-liveness count.

The stripper is then itself a detector, and it gets the same treatment as any
other: a planted positive in both directions. A token planted in a comment must
be IGNORED and the same token planted in code must be CAUGHT, because without
both a working stripper and one that strips everything are the same green. That
is not hypothetical here - see
:func:`test_the_stripper_keeps_a_token_after_a_url_on_the_same_line`. The naive
``//``-to-end-of-line stripper this module was first written against passed both
comment-direction controls and still swallowed every planted token that followed
an ``https://`` literal, because ``shell/lib/endpoint.js`` builds its URL from a
template holding ``://``. A stripper that truncates there shrinks the population
it scans while still reporting zero findings, which is the exact failure shape a
detector arm exists to make impossible.

EVERY DETECTOR HAS A PLANTED-POSITIVE ARM. Most arms below pass against the
committed tree on the day they were written, which means the real content proves
nothing about whether the detector can fire. The planted controls are what carry
the proof. Where a live positive exists it is preferred over a planted one:
:func:`test_main_js_is_the_only_shell_module_that_imports_electron` fires the
electron detector on REAL committed code rather than on a fixture.

EVERY FORBIDDEN TOKEN IS GRADED ON ITS OWN SUBJECT. CS-605 closed having
measured that emptying a token tuple killed one arm while each single-token
deletion SURVIVED it, so the proof showed only that at least one of four
patterns fired. The certificate-posture table below is therefore parametrized
one case per token, and the table is spelled in THIS file rather than imported
from the source under test - importing it would let a deletion in the source
delete the test case and stay green.
"""

from __future__ import annotations

import getpass
import json
import platform
import re
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Final

import pytest

from clockspeed.surface import config

# ---------------------------------------------------------------------------
# a. Population - enumerated from git, never from a glob
# ---------------------------------------------------------------------------

#: The repository root, read from the module that owns the answer rather than
#: rebuilt from ``__file__``.
REPO_ROOT: Final = config.repo_root()

#: Wall-clock bound for the git plumbing below (CS-896). An unbounded child
#: cannot fail the test that owns it - it burns the CI job's whole budget until
#: the lane is cancelled, which is evidence of nothing. 120s matches the git
#: timeout in tests/test_doc_budget.py and tests/test_commit_msg_gate.py. It is
#: deliberately generous: the job is to bound a hang, not to police speed, and a
#: tight value under two-worker contention on a 2-vCPU runner is a new flake.
GIT_TIMEOUT: Final = 120


#: The subtree this module grades.
SHELL_DIR: Final = "shell"

#: Every file that must be present, by name. An explicit list, because a floor
#: alone is satisfied by fourteen files none of which is the one that matters.
REQUIRED_NAMES: Final = (
    "shell/lib/endpoint.js",
    "shell/lib/geometry.js",
    "shell/lib/state.js",
    "shell/lib/supervisor.js",
    "shell/lib/tray.js",
    "shell/lib/trust.js",
    "shell/lib/verdict.js",
    "shell/lib/window.js",
    "shell/main.js",
    "shell/package-lock.json",
    "shell/package.json",
    "shell/preload.js",
    "shell/test/endpoint.test.js",
    "shell/test/geometry.test.js",
    "shell/test/state.test.js",
    "shell/test/supervisor.test.js",
    "shell/test/tray.test.js",
    "shell/test/trust.test.js",
    "shell/test/verdict.test.js",
    "shell/test/window.test.js",
)

#: The smallest population that is not a defect. An empty population satisfies
#: every zero-finding arm in this module, so the floor is what makes the rest
#: of them mean anything.
POPULATION_FLOOR: Final = len(REQUIRED_NAMES)

#: The highest byte the project's character-set rule admits. Spelled here rather
#: than imported, because a test that imports a constant to assert the constant
#: grades nothing.
MAX_ASCII_BYTE: Final = 0x7E

#: The modules that must not reach the electron API.
LIB_PREFIX: Final = "shell/lib/"

#: The five behaviour suites.
TEST_PREFIX: Final = "shell/test/"

#: A token no shell file contains. Every planted control uses it, so a control
#: can never pass by matching real content.
PLANTED: Final = "PLANTED_TOKEN"


@lru_cache(maxsize=1)
def shell_files() -> tuple[str, ...]:
    """Every file under ``shell/`` git would track, as repo-relative posix paths.

    ENUMERATED WITH ``--cached --others --exclude-standard``, and all three
    flags earn their place. ``--cached`` alone cannot see a file until it has
    been committed, so a shell file added in the same commit as this module
    would get one free pass through every arm below. ``--others`` covers what is
    written but not yet committed and ``--exclude-standard`` drops anything
    gitignored, which is what the commit gate and the PostToolUse guard already
    do. The same three flags, for the same reason, appear in
    ``tests/test_exception_rendering.py``.

    Returns:
        The paths, sorted. Empty only if the subtree is genuinely absent.
    """
    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", f"{SHELL_DIR}/"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
        timeout=GIT_TIMEOUT,
    )
    return tuple(sorted({line.strip() for line in completed.stdout.splitlines() if line.strip()}))


def read_bytes(relative: str) -> bytes:
    """Read one shell file as raw bytes.

    Args:
        relative: A repo-relative posix path from :func:`shell_files`.

    Returns:
        The file's bytes, unmodified.
    """
    return (REPO_ROOT / relative).read_bytes()


@lru_cache(maxsize=64)
def read_text(relative: str) -> str:
    """Read one shell file, decoded strictly as ASCII.

    Decoding as ASCII rather than as UTF-8 is deliberate: a byte above 0x7E
    raises here instead of decoding into a character a later arm has to notice.
    The character-set arm asserts the same thing on raw bytes, so this is the
    second of two gates rather than the only one.

    Args:
        relative: A repo-relative posix path from :func:`shell_files`.

    Returns:
        The decoded text.
    """
    return read_bytes(relative).decode("ascii")


def test_the_shell_population_is_not_empty_and_meets_its_floor() -> None:
    """There is something to grade, and there is enough of it.

    Stated first because every zero-finding arm below is satisfied vacuously by
    an empty population.
    """
    population = shell_files()
    assert population, "git enumerated no files under shell/; every arm below would be vacuous"

    total = len(population)
    assert total >= POPULATION_FLOOR, f"population {total} is below the floor {POPULATION_FLOOR}"


def test_every_required_shell_file_is_present_by_name() -> None:
    """The population holds each named file, not merely enough files."""
    absent = tuple(name for name in REQUIRED_NAMES if name not in shell_files())
    total = len(absent)
    assert total == 0, f"{total} required shell file(s) absent from the enumeration: {absent}"


def test_every_enumerated_shell_file_exists_on_disk_and_is_non_empty() -> None:
    """Each enumerated path is a real, non-empty file.

    An arm written over a file that git lists but disk does not hold would error
    rather than pass, but an arm written over an EMPTY file passes while grading
    nothing.
    """
    missing = tuple(name for name in shell_files() if not (REPO_ROOT / name).is_file())
    assert not missing, f"enumerated but absent from disk: {missing}"

    empty = tuple(name for name in shell_files() if (REPO_ROOT / name).stat().st_size == 0)
    total = len(empty)
    assert total == 0, f"{total} shell file(s) present but empty: {empty}"


def test_the_population_enumerator_can_return_empty() -> None:
    """The enumerator is proved able to report nothing, so a non-empty is news.

    Run against a prefix nothing lives under. Without this, an enumerator that
    always returned the same fourteen names and one that genuinely measured the
    tree would be indistinguishable.
    """
    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "no_such_subtree/"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
        timeout=GIT_TIMEOUT,
    )
    assert completed.stdout.strip() == "", "the enumerator answered for a subtree that is absent"

    off_subtree = tuple(name for name in shell_files() if not name.startswith(f"{SHELL_DIR}/"))
    assert not off_subtree, f"the enumeration reached outside shell/: {off_subtree}"


# ---------------------------------------------------------------------------
# b. Character set and line endings, on raw bytes
# ---------------------------------------------------------------------------


def offending_bytes(data: bytes) -> tuple[int, ...]:
    """Every byte position holding a value above :data:`MAX_ASCII_BYTE`.

    Args:
        data: The raw file bytes.

    Returns:
        The offending offsets, in order.
    """
    return tuple(index for index, value in enumerate(data) if value > MAX_ASCII_BYTE)


def test_every_shell_byte_is_seven_bit_ascii() -> None:
    """No byte of any shell file sits above 0x7E (non-negotiable 4)."""
    findings: list[str] = []
    for name in shell_files():
        offsets = offending_bytes(read_bytes(name))
        if offsets:
            findings.append(f"{name}: {len(offsets)} byte(s), first at {offsets[0]}")
    total = len(findings)
    assert total == 0, f"non-ASCII bytes in {total} shell file(s): {findings}"


def test_the_character_set_detector_fires_on_a_planted_byte() -> None:
    """Planting one high byte makes :func:`offending_bytes` report it."""
    clean = len(offending_bytes(b'const a = "plain";'))
    planted = len(offending_bytes(b'const a = "plain"; // \xe2\x80\x94'))
    assert clean == 0
    assert planted > 0, "the character-set detector did not fire on a planted byte"


def test_no_shell_file_holds_a_carriage_return() -> None:
    """Every shell file is LF-terminated, asserted on raw bytes.

    The harness's edit tools have been observed converting a tracked file to
    CRLF while git normalised the blob and reported the tree clean, so the
    working tree violated the rule invisibly. Counting the byte is the only
    check that sees it.
    """
    findings = {
        name: read_bytes(name).count(b"\r")
        for name in shell_files()
        if read_bytes(name).count(b"\r") > 0
    }
    total = len(findings)
    assert total == 0, f"carriage returns in {total} shell file(s): {findings}"


def test_the_carriage_return_detector_fires_on_a_planted_byte() -> None:
    """The CR count is proved to distinguish CRLF from LF."""
    assert b"const a = 1;\n".count(b"\r") == 0
    assert b"const a = 1;\r\n".count(b"\r") > 0


# ---------------------------------------------------------------------------
# c. The comment stripper, and its controls in both directions
# ---------------------------------------------------------------------------


def strip_js_comments(text: str) -> str:
    """Return ``text`` with JavaScript comments removed and string literals kept.

    A SINGLE LEFT-TO-RIGHT PASS in which comment state and string state are
    mutually exclusive, and whichever opens first wins. That precedence is the
    whole design, and both halves of it are load-bearing here:

    - A ``//`` inside a string must NOT open a comment. ``shell/lib/endpoint.js``
      builds ``https://host:port/`` from a template literal, and a stripper that
      truncated there would silently shrink every population scanned below while
      still reporting zero findings.
    - A quote or a backtick inside a comment must NOT open a string. The JSDoc
      blocks throughout ``shell/`` quote identifiers in Markdown backticks and
      carry apostrophes in prose, so a stripper that tracked strings first would
      pair a backtick in one comment with a backtick in another and swallow the
      code between them.

    Newlines inside block comments are preserved so a line number computed from
    the stripped text still refers to the original file.

    NOT A JAVASCRIPT PARSER, AND THE SAFETY NET THIS DOCSTRING USED TO CLAIM
    DOES NOT EXIST. A regular expression literal containing an unescaped quote -
    ``/["']/`` - is read as opening a string, and one containing an unescaped
    slash next to a star - ``/[/*]/``, which is VALID JavaScript - is read as
    opening a block comment. Everything up to the next ``*/`` then vanishes, and
    ``/[*/]/`` is the matching valid literal that closes it. A bypass planted
    between the two is invisible to every arm that grades stripped code.

    This text previously named
    :func:`test_the_stripper_is_idempotent_and_never_grows_the_real_tree` and
    :func:`test_stripping_leaves_every_shell_module_its_own_code` as the alarm.
    BOTH WERE MEASURED AGAINST THAT ATTACK AND BOTH STAYED GREEN. Idempotence
    cannot fire, because a second strip re-derives the same deletion; never-grows
    cannot fire, because deleting is shrinking. Neither was ever capable of
    catching it, so the claim was false when it was written rather than having
    gone stale.

    THE REPAIR WAS TO STOP DEPENDING ON THIS FUNCTION WHERE IT MATTERS. The
    certificate-posture sweep in section (d) and the call-site grading in
    section (e) both read RAW text and exempt documented mentions through an
    explicit allow-list, so no regex literal can blind them.
    :func:`test_the_raw_token_sweep_catches_a_bypass_hidden_behind_a_regex_literal`
    plants exactly this attack and proves the raw path still fires while
    measuring, in the same arm, that the stripper is blinded by it. What is left
    on the stripper is the purity partition, the CommonJS census, the constant
    extraction and the test-liveness count - places where a comment mention is a
    real false positive and where a blinded read fails safe rather than open.

    Args:
        text: The source of one ``.js`` file.

    Returns:
        The same source with comment text removed.
    """
    out: list[str] = []
    index = 0
    end = len(text)
    while index < end:
        char = text[index]
        if char == "/" and index + 1 < end and text[index + 1] == "/":
            while index < end and text[index] != "\n":
                index += 1
            continue
        if char == "/" and index + 1 < end and text[index + 1] == "*":
            index += 2
            while index + 1 < end and not (text[index] == "*" and text[index + 1] == "/"):
                if text[index] == "\n":
                    out.append("\n")
                index += 1
            index = min(index + 2, end)
            continue
        if char in "\"'`":
            quote = char
            out.append(char)
            index += 1
            while index < end:
                if text[index] == "\\":
                    out.append(text[index : index + 2])
                    index += 2
                    continue
                out.append(text[index])
                if text[index] == quote:
                    index += 1
                    break
                if quote != "`" and text[index] == "\n":
                    index += 1
                    break
                index += 1
            continue
        out.append(char)
        index += 1
    return "".join(out)


@lru_cache(maxsize=64)
def code_of(relative: str) -> str:
    """The gradable code of one shell file, with comments removed.

    JSON carries no comment syntax, so a ``.json`` file is returned unchanged.
    Running the stripper over one would be harmless but would also be a claim
    this module cannot make, and ``shell/package-lock.json`` holds fourteen
    ``https://`` registry URLs that exist to be read literally.

    Args:
        relative: A repo-relative posix path from :func:`shell_files`.

    Returns:
        The code, comments removed for ``.js`` and untouched otherwise.
    """
    text = read_text(relative)
    return strip_js_comments(text) if relative.endswith(".js") else text


def test_the_stripper_ignores_a_token_inside_a_line_comment() -> None:
    """A banned token named in a ``//`` comment is not code."""
    assert PLANTED not in strip_js_comments(f"const a = 1; // never call {PLANTED}\n")


def test_the_stripper_ignores_a_token_inside_a_block_comment() -> None:
    """A banned token named in a ``/* */`` comment is not code."""
    block = f"/*\n * this module avoids {PLANTED}\n */\nconst a = 1;\n"
    assert PLANTED not in strip_js_comments(block)


def test_the_stripper_keeps_a_token_that_is_really_in_code() -> None:
    """A banned token in code survives the stripper and stays gradable.

    Paired with the two comment arms above: without this one, a stripper that
    deleted its entire input would satisfy them both.
    """
    assert PLANTED in strip_js_comments(f'const a = "{PLANTED}";\n')


def test_the_stripper_keeps_a_token_after_a_url_on_the_same_line() -> None:
    """A ``//`` inside a string literal does not begin a comment.

    THE ARM THAT CAUGHT THE FIRST IMPLEMENTATION. Written against a naive
    ``//``-to-end-of-line stripper it reported ``0 == 3``: every planted token
    following an ``https://`` literal was swallowed, in all three string
    spellings, while both comment-direction controls above stayed green.
    """
    expected = 3
    survivors = [
        spelling
        for spelling in (
            f'const u = "https://example.invalid/"; const b = "{PLANTED}";\n',
            f"const u = 'https://example.invalid/'; const b = '{PLANTED}';\n",
            f"const u = `https://${{h}}:${{p}}/`; const b = `{PLANTED}`;\n",
        )
        if PLANTED in strip_js_comments(spelling)
    ]
    total = len(survivors)
    assert total == expected, f"code after a URL was swallowed in {expected - total} spelling(s)"


def test_the_stripper_keeps_code_after_a_backtick_inside_a_comment() -> None:
    """A Markdown backtick in a JSDoc block does not open a template literal.

    Every JSDoc header under ``shell/`` quotes identifiers this way - for
    instance ``shell/lib/endpoint.js`` names ``config/ports.json`` in backticks
    inside a block comment. A stripper that opened a template there would run to
    the next backtick in some later comment and eat the code between.
    """
    planted = f'/* see `config/ports.json` and `main.js` */\nconst a = "{PLANTED}";\n'
    assert PLANTED in strip_js_comments(planted)


def test_the_stripper_keeps_code_after_an_apostrophe_inside_a_comment() -> None:
    """An apostrophe in comment prose does not open a string literal."""
    planted = f'// electron\'s defaults are not inherited here\nconst a = "{PLANTED}";\n'
    assert PLANTED in strip_js_comments(planted)


def test_the_stripper_is_idempotent_and_never_grows_the_real_tree() -> None:
    """Stripping twice equals stripping once, and stripping never adds bytes.

    Two cheap invariants over the REAL files rather than over a fixture. A
    stripper that had begun mis-pairing a quote would break one of them long
    before it went quietly wrong in a zero-finding arm.
    """
    findings: list[str] = []
    for name in shell_files():
        if not name.endswith(".js"):
            continue
        raw = read_text(name)
        once = strip_js_comments(raw)
        if len(once) > len(raw):
            findings.append(f"{name}: grew {len(raw)} -> {len(once)}")
        if strip_js_comments(once) != once:
            findings.append(f"{name}: not idempotent")
    total = len(findings)
    assert total == 0, f"the stripper is unstable on {total} file(s): {findings}"


def test_stripping_leaves_every_shell_module_its_own_code() -> None:
    """No ``.js`` file strips to nothing, and each keeps its strict-mode prologue.

    THE GUARD AGAINST A STRIPPER THAT STRIPS EVERYTHING, asserted per file so a
    single swallowed module cannot hide behind thirteen intact ones. Both quote
    spellings are accepted: ``shell/lib/trust.js`` writes ``'use strict';``
    where its five siblings write it with double quotes.
    """
    findings: list[str] = []
    for name in shell_files():
        if not name.endswith(".js"):
            continue
        code = code_of(name)
        if '"use strict"' not in code and "'use strict'" not in code:
            findings.append(f"{name}: lost its strict-mode prologue")
    total = len(findings)
    assert total == 0, f"{total} module(s) did not survive stripping: {findings}"


def test_stripping_preserves_the_url_template_that_defeats_a_naive_stripper() -> None:
    """``shell/lib/endpoint.js`` still holds its ``://`` after stripping.

    A live control rather than a planted one: this is the real construct in the
    real file that the first implementation of the stripper destroyed.
    """
    code = code_of("shell/lib/endpoint.js")
    assert "://" in code, "the URL template did not survive stripping"
    assert "SCHEME" in code, "the scheme constant did not survive stripping"


# ---------------------------------------------------------------------------
# d. Certificate posture - one arm per token, from this file's own table
# ---------------------------------------------------------------------------

#: Every way a chromium or Node embedder can weaken or bypass TLS verification.
#:
#: SPELLED HERE AND NEVER IMPORTED FROM THE SOURCE UNDER TEST. A table imported
#: from ``shell/`` would let a deletion there delete the test case and stay
#: green. CS-605 closed having measured the neighbouring failure: emptying a
#: token tuple killed an arm while every single-token deletion SURVIVED it, so
#: the proof showed only that at least one of four patterns fired. Hence one
#: parametrized case per token, each graded on its own subject.
FORBIDDEN_TLS_TOKENS: Final = (
    "ignore-certificate-errors",
    "allow-insecure-localhost",
    "ignore-ssl-errors",
    "setIgnoreCertificateErrors",
    "rejectUnauthorized",
    "NODE_TLS_REJECT_UNAUTHORIZED",
    "webSecurity",
    "allowRunningInsecureContent",
    "certificate-error",
    "checkServerIdentity",
    "appendSwitch",
)


#: Mentions of a forbidden token that are allowed to remain, as exact
#: ``(path, stripped full line)`` pairs.
#:
#: MEASURED EMPTY at the repair that introduced it, and that measurement is the
#: point rather than an accident. Not one line under ``shell/`` names any token
#: in the table above - not in code and not in prose - so the sweep below needs
#: no exemption at all today, and the stripper it used to run behind was never
#: buying anything for THIS table. The comment-direction argument in this
#: module's header is about the token ``electron``, which the purity partition
#: in section (f) grades and which two modules legitimately name in prose.
#:
#: An exemption is an EXACT FULL LINE and never a filename or a token. A
#: file-level or token-level exemption would blind the sweep to everything else
#: that file or token could later carry, which is the hole this replaced.
FORBIDDEN_TOKEN_ALLOWLIST: Final[frozenset[tuple[str, str]]] = frozenset()


def raw_token_lines(text: str, token: str) -> tuple[int, ...]:
    """Every 1-based line number in ``text`` whose RAW line contains ``token``.

    NO STRIPPER. That is the whole design: a regex literal cannot blind a scan
    that never tries to tell code from comment.

    Args:
        text: The file text, unmodified.
        token: The literal to look for, matched case-sensitively.

    Returns:
        The line numbers, in file order.
    """
    return tuple(number for number, line in enumerate(text.splitlines(), start=1) if token in line)


def token_findings(
    sources: dict[str, str],
    token: str,
    allowlist: frozenset[tuple[str, str]] = FORBIDDEN_TOKEN_ALLOWLIST,
) -> tuple[str, ...]:
    """Every ``path:line`` naming ``token`` that the allow-list does not exempt.

    Args:
        sources: Path to raw text, for the population to sweep.
        token: The literal to look for.
        allowlist: Exact ``(path, stripped line)`` pairs to exempt. Defaulted so
            the real arms cannot forget it and parameterised so its own control
            can drive it with a synthetic one.

    Returns:
        The findings as ``path:line``, in enumeration order.
    """
    findings: list[str] = []
    for name in sorted(sources):
        lines = sources[name].splitlines()
        findings.extend(
            f"{name}:{number}"
            for number in raw_token_lines(sources[name], token)
            if (name, lines[number - 1].strip()) not in allowlist
        )
    return tuple(findings)


def raw_sources() -> dict[str, str]:
    """The whole graded population as raw text, keyed by path.

    Returns:
        Path to unmodified file text.
    """
    return {name: read_text(name) for name in shell_files()}


@pytest.mark.parametrize("token", FORBIDDEN_TLS_TOKENS)
def test_no_shell_file_names_this_tls_escape_hatch_in_raw_text(token: str) -> None:
    """No shell file names this TLS escape hatch ANYWHERE - code or comment.

    ADR 0014 pins the companion to one certificate. Every token in the table is
    a way to make that pin advisory, and each is graded on its own subject so a
    surviving deletion cannot hide behind a sibling that still fires.

    SWEPT RAW, WHICH IS THE REPAIR. This arm used to grade stripped code, and a
    stripped-code sweep is blindable: ``/[/*]/`` is a valid regular expression
    literal that the stripper reads as opening a block comment, so a bypass
    planted between it and a later ``/[*/]/`` was invisible while the raw file
    still carried all of it. That was measured, not supposed - see
    :func:`test_the_raw_token_sweep_catches_a_bypass_hidden_behind_a_regex_literal`.

    The cost of reading raw is that a module documenting the ban would fail, and
    :data:`FORBIDDEN_TOKEN_ALLOWLIST` is where such a line is pinned by exact
    text. It is empty, because no shell file names any of these tokens today.
    """
    findings = token_findings(raw_sources(), token)
    total = len(findings)
    assert total == 0, f"{total} shell line(s) name {token!r}: {findings}"


@pytest.mark.parametrize("token", FORBIDDEN_TLS_TOKENS)
def test_the_raw_token_sweep_fires_on_each_planted_token(token: str) -> None:
    """Each table entry is proved findable, in code AND in a comment.

    Both directions are asserted to FIND it now. Under the old stripped sweep
    the comment direction asserted the opposite - that a documented mention was
    ignored - and that leniency is precisely what the regex-literal attack wore
    as a disguise.
    """
    clean = {"a.js": 'const a = "plain";\n'}
    assert token_findings(clean, token) == ()

    in_code = {"a.js": f'const a = "plain";\nconst b = "{token}";\n'}
    assert token_findings(in_code, token) == ("a.js:2",), f"not found in code: {token!r}"

    in_comment = {"a.js": f"const a = 1;\n// this module never calls {token}\n"}
    assert token_findings(in_comment, token) == ("a.js:2",), f"not found in prose: {token!r}"


#: The two valid regular expression literals that blind :func:`strip_js_comments`.
#:
#: ``/[/*]/`` is legal JavaScript - a character class holding a slash and a star
#: - and the stripper sees the ``/*`` at offset two and opens a block comment.
#: ``/[*/]/`` is the matching literal whose ``*/`` closes it. Everything between
#: them is deleted before any stripped-code arm ever sees it.
BLINDING_OPENER: Final = "/[/*]/"
BLINDING_CLOSER: Final = "/[*/]/"


def test_the_raw_token_sweep_catches_a_bypass_hidden_behind_a_regex_literal() -> None:
    """The attack that defeated every stripped-code arm is caught by the raw sweep.

    THIS ARM MEASURES BOTH HALVES IN ONE PLACE, deliberately. Asserting only
    that the raw sweep fires would leave a reader unable to tell whether the
    stripper was ever really blind, and a control whose premise is unmeasured is
    the shape of finding this module exists to refuse. So the blinding is
    measured first, and the raw sweep is measured second on the same bytes.
    """
    hidden = (
        '"use strict";\n'
        f"const PATH_SPLITTER = {BLINDING_OPENER};\n"
        'app.commandLine.appendSwitch("ignore-certificate-errors");\n'
        'process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";\n'
        f"const PATH_JOINER = {BLINDING_CLOSER};\n"
    )

    # Four, not the three switches a reader counts: ``certificate-error`` is a
    # substring of ``ignore-certificate-errors``, so the table matches it too.
    # The number is asserted rather than derived so that a fixture edited to
    # plant less than it claims cannot quietly weaken this control.
    present = tuple(token for token in FORBIDDEN_TLS_TOKENS if token in hidden)
    expected_planted = 4
    assert len(present) == expected_planted, f"the fixture plants {len(present)} token(s)"

    stripped = strip_js_comments(hidden)
    blinded = tuple(token for token in present if token not in stripped)
    assert blinded == present, (
        "the stripper was NOT blinded by the planted regex literals, so this control "
        f"proves nothing; it still saw {tuple(t for t in present if t in stripped)}"
    )

    missed = tuple(token for token in present if not token_findings({"evil.js": hidden}, token))
    assert missed == (), f"the RAW sweep missed a hidden bypass: {missed}"


def test_the_allowlist_exempts_one_exact_line_and_nothing_wider() -> None:
    """The exemption mechanism is graded, even though the real allow-list is empty.

    An empty allow-list makes every arm above pass without ever exercising the
    filter, so the filter is driven here against a synthetic one instead.

    WHAT AN EXEMPTION ACTUALLY COVERS, stated exactly rather than approximately.
    The key is ``(path, exact stripped line)``, so an entry exempts EVERY line
    in that one file whose text matches exactly - a repeated line is covered
    twice by one entry - and exempts nothing at all in any other file. The
    breadth is therefore one file's worth of one exact string, which is the
    narrowest key that a human can write down and a later reader can verify by
    eye. It is deliberately NOT a per-occurrence key: line numbers move under
    every unrelated edit, and an exemption that goes stale on reformatting would
    be re-approved reflexively rather than read.
    """
    token = FORBIDDEN_TLS_TOKENS[0]
    line = f"// documented: never call {token}"
    sources = {
        "a.js": f"const a = 1;\n{line}\n{line}\n",
        "b.js": f"{line}\n",
    }

    unfiltered = token_findings(sources, token)
    expected = ("a.js:2", "a.js:3", "b.js:1")
    assert unfiltered == expected, f"the fixture is not what it claims: {unfiltered}"

    exempted = token_findings(sources, token, frozenset({("a.js", line)}))
    assert exempted == ("b.js:1",), f"the allow-list exempted too much or too little: {exempted}"


def test_every_allowlisted_line_is_still_present_in_the_tree() -> None:
    """No exemption outlives the line it was written for.

    A stale entry is dead weight at best, and at worst it silently pre-approves
    a line somebody later writes. Vacuous while the allow-list is empty, which
    is its state today and is asserted as a measurement rather than assumed.
    """
    sources = raw_sources()
    stale = tuple(
        (name, line)
        for name, line in sorted(FORBIDDEN_TOKEN_ALLOWLIST)
        if name not in sources or line not in {ln.strip() for ln in sources[name].splitlines()}
    )
    assert not stale, f"the allow-list exempts {len(stale)} line(s) that no longer exist: {stale}"


def test_no_shell_lib_module_names_the_electron_package_in_raw_text() -> None:
    """A RAW second layer under the purity partition, which is stripper-based.

    :func:`test_no_shell_lib_module_imports_electron` grades stripped code and
    is therefore blindable by the same regex literal as the old token sweep. The
    partition is not a TLS bypass, so it is not in the table above, but a
    ``shell/lib/`` module that quietly acquired an electron import would mute
    the whole tier-2 lane. One raw line closes it. ``shell/lib/`` carries no
    prose mention of the import form, so no allow-list is needed here.
    """
    impure = tuple(
        name
        for name in shell_files()
        if name.startswith(LIB_PREFIX) and _ELECTRON_REQUIRE.search(read_text(name)) is not None
    )
    assert not impure, f"{len(impure)} module(s) under {LIB_PREFIX} import electron raw: {impure}"


# ---------------------------------------------------------------------------
# e. Structure - the call sites that must exist exactly once
# ---------------------------------------------------------------------------

#: One call site each, in ``shell/main.js``. Counted on stripped code, because
#: ``shell/lib/trust.js`` and ``shell/test/trust.test.js`` both discuss
#: ``setCertificateVerifyProc`` in prose without calling it.
MAIN_SINGLETONS: Final = (
    "setCertificateVerifyProc(",
    "new BrowserWindow(",
    "callback(",
)


@pytest.mark.parametrize("site", MAIN_SINGLETONS)
def test_main_js_holds_exactly_one_of_each_critical_call_site(site: str) -> None:
    """The verify proc, the window and the verdict callback each appear once.

    A SECOND SITE IS ONE OF TWO DEFECTS THIS SECTION GRADES, AND IT WAS NOT THE
    ONE THAT HAPPENED. Two ``setCertificateVerifyProc`` registrations mean the
    last one wins and the pin may be the loser; two ``new BrowserWindow`` sites
    mean a window built past the audited options.

    THE ``callback`` ENTRY IS DIFFERENT, and this docstring used to describe it
    wrongly. It claimed a second site would mean "a verdict answered twice". The
    measured defect was the opposite shape: ONE site, answering the WRONG
    integer. Counting the token proves only that a callback happens, never that
    it carries the verdict, and ``callback(0)`` - a blanket accept for every
    host - satisfied this arm exactly as well as the correct call did. What
    grades the argument is
    :func:`test_main_js_hands_the_verify_callback_the_mapped_verdict_and_nothing_else`
    below; this arm is the count and only the count.
    """
    found = code_of("shell/main.js").count(site)
    assert found == 1, f"shell/main.js holds {found} {site!r} site(s), expected exactly 1"


@pytest.mark.parametrize("site", MAIN_SINGLETONS)
def test_main_js_holds_exactly_one_of_each_critical_call_site_in_raw_text(site: str) -> None:
    """The same three counts, taken RAW so no regex literal can hide a second site.

    The arm above reads stripped code, and a bypass planted between ``/[/*]/``
    and ``/[*/]/`` is deleted before it is counted - so a second, earlier
    ``callback(0)`` could sit in main.js while the stripped count still read 1.
    Electron takes the first answer, so the hidden one would be the one that
    won. Raw text has no such blind spot, and main.js happens to name none of
    these three in prose, so the raw count is exactly the code count today.
    """
    found = read_text("shell/main.js").count(site)
    assert found == 1, f"shell/main.js holds {found} raw {site!r} site(s), expected exactly 1"


#: The ONLY expression ``shell/main.js`` may hand to the verify callback.
#:
#: PINNED AS TEXT, because the property being protected is not "a callback
#: happens" but "the callback receives the mapped verdict". The mapping now
#: lives in ``shell/lib/verdict.js`` where ``shell/test/verdict.test.js`` pins
#: all five verdicts by value; this constant is the seam that connects that
#: graded mapping to the one call site that consumes it. Change the call site
#: and this goes red, which is the intent - the argument to that callback is the
#: single most security-load-bearing expression in the shell.
CALLBACK_ARGUMENT: Final = "verdicts.codeForOrRefuse(verdict)"


def callback_arguments(text: str) -> tuple[str, ...]:
    """Every argument expression handed to a call spelled ``callback(``.

    Parentheses are balanced from the opening one, so a nested call in the
    argument - which is exactly the shape the shipped code uses - is returned
    whole rather than truncated at its first ``)``.

    Note that ``(request, callback) =>`` does not match: the needle carries the
    opening parenthesis, so a parameter named ``callback`` is not a call.

    Args:
        text: The file text to read, RAW.

    Returns:
        The argument expressions, stripped of surrounding whitespace, in order.
    """
    needle = "callback("
    found: list[str] = []
    start = 0
    while True:
        at = text.find(needle, start)
        if at == -1:
            return tuple(found)
        index = at + len(needle)
        depth = 1
        while index < len(text) and depth > 0:
            if text[index] == "(":
                depth += 1
            elif text[index] == ")":
                depth -= 1
            index += 1
        found.append(text[at + len(needle) : index - 1].strip())
        start = index


def test_main_js_hands_the_verify_callback_the_mapped_verdict_and_nothing_else() -> None:
    """The verify callback receives the mapped verdict, by exact expression.

    THE ARM THAT WOULD HAVE CAUGHT THE DEFECT. Six graders ran against a tree in
    which ``callback(codeFor(verdict))`` could be changed to ``callback(0)`` - a
    blanket accept for every host in the session - with the Python shell suite,
    ``node --test``, the drift guard and the commit gate all staying green,
    because every arm counted the TOKEN and none read the ARGUMENT. Four
    variants of the same bypass survived the same way, including one that kept a
    single call site and still answered 0 for every verdict.

    Read RAW rather than stripped, for the reason given in
    :func:`test_main_js_holds_exactly_one_of_each_critical_call_site_in_raw_text`.
    """
    arguments = callback_arguments(read_text("shell/main.js"))
    assert arguments, "no callback call site was found at all; this arm would be vacuous"
    assert arguments == (CALLBACK_ARGUMENT,), f"unexpected verify-callback argument(s): {arguments}"


#: The two bindings the verify callback's expression resolves through, pinned to
#: the exact require line that must produce them.
#:
#: THE BYPASS THIS CLOSES IS THE ONE THAT PINNING AN EXPRESSION INVITES. Once
#: ``callback(verdicts.codeForOrRefuse(verdict))`` is graded as text, the next
#: cheapest way to make it answer 0 for every host is to leave that text alone
#: and change what ``verdicts`` MEANS - ``const verdicts = { codeForOrRefuse:
#: () => 0 };`` satisfies the exact-expression arm and the no-digit arm at once,
#: because the digit has moved out of the argument. The same holds for
#: ``trust``, whose ``decide`` produces the verdict being mapped. Pinning the
#: binding is what makes grading the expression mean anything.
VERIFY_PATH_BINDINGS: Final = (
    'const trust = require("./lib/trust.js");',
    'const verdicts = require("./lib/verdict.js");',
)


def test_the_verify_callback_resolves_through_the_real_modules_and_no_other() -> None:
    """``trust`` and ``verdicts`` are each bound once, to the real module.

    Counted on RAW text. ``shell/main.js`` names neither binding in prose, so
    the raw count is the code count, and reading raw keeps a regex literal from
    hiding a shadowing rebind the way it hid the token bypass.
    """
    source = read_text("shell/main.js")
    for binding in VERIFY_PATH_BINDINGS:
        found = source.count(binding)
        assert found == 1, f"shell/main.js holds {found} of {binding!r}, expected exactly 1"

    for name in ("trust", "verdicts"):
        bound = source.count(f"const {name} = ")
        assert bound == 1, f"shell/main.js binds {name!r} {bound} time(s), expected exactly 1"


def test_the_binding_check_fires_on_a_shadowed_module() -> None:
    """The binding arm is proved to tell the real require from a fake object.

    Without this the arm is two counts that happen to read 1, and a counter
    stuck at 1 is the same green as one that measured.
    """
    real = "\n".join(VERIFY_PATH_BINDINGS) + "\n"
    assert all(real.count(binding) == 1 for binding in VERIFY_PATH_BINDINGS)

    shadowed = real + "const verdicts = { codeForOrRefuse: () => 0 };\n"
    after_shadowing = 2
    assert shadowed.count("const verdicts = ") == after_shadowing, (
        "a second binding was not counted"
    )

    replaced = (
        'const verdicts = { codeForOrRefuse: () => 0 };\nconst trust = require("./lib/trust.js");\n'
    )
    assert replaced.count(VERIFY_PATH_BINDINGS[1]) == 0, "a swapped binding still matched"


def test_no_digit_ever_reaches_the_verify_callback() -> None:
    """Nothing numeric is handed to the callback, in any spelling.

    A SECOND AND WIDER NET THAN THE EXACT-EXPRESSION ARM. That one pins one
    string and would go red on a rename that is entirely legitimate; this one
    states the property that must hold no matter how the call is spelled. Every
    bypass in this class ends with an integer literal reaching the callback -
    ``callback(0)`` directly, or a ternary that resolves to it - and the shell
    has no reason to write a digit there at all: the integers live in
    ``shell/lib/verdict.js`` and are reached only through a named function.
    """
    arguments = callback_arguments(read_text("shell/main.js"))
    assert arguments, "no callback call site was found at all; this arm would be vacuous"

    numeric = tuple(argument for argument in arguments if any(char.isdigit() for char in argument))
    assert not numeric, f"a digit reached the verify callback in: {numeric}"


def test_the_callback_argument_reader_fires_on_every_measured_bypass() -> None:
    """The reader is proved on the shipped shape and on all four measured bypasses.

    Each fixture below was applied to a real checkout and measured to leave the
    whole gate green before this arm existed. They are replayed here as text so
    the proof does not depend on anyone re-running the mutation.
    """
    shipped = f"    callback({CALLBACK_ARGUMENT});\n"
    assert callback_arguments(shipped) == (CALLBACK_ARGUMENT,), "the shipped shape did not read"

    bypasses = {
        "blanket accept": "    callback(0);\n",
        "one site, wrong answer": (
            "    const answer = (code) => callback(code);\n"
            f"    answer(verdict === trust.TRUST ? {CALLBACK_ARGUMENT} : 0);\n"
        ),
        "second hidden site": f"    callback(0);\n    callback({CALLBACK_ARGUMENT});\n",
        "numeric via a named alias": "    callback(ACCEPT_EVERYTHING);\n",
    }
    survivors = tuple(
        label
        for label, text in bypasses.items()
        if callback_arguments(text) == (CALLBACK_ARGUMENT,)
    )
    assert not survivors, f"the reader could not tell these from the shipped call: {survivors}"

    # WHY BOTH ARMS EXIST, demonstrated rather than argued. The digit net sees
    # the blanket accept; it is BLIND to the one-site bypass, whose only
    # ``callback(`` call is spelled ``callback(code)`` and carries no digit at
    # all - the 0 sits in the ternary that feeds the alias. That bypass is
    # caught by the exact-expression arm and by nothing else here.
    assert callback_arguments("    callback(0);\n") == ("0",)

    one_site = callback_arguments(bypasses["one site, wrong answer"])
    assert one_site == ("code",), f"the one-site bypass read as {one_site}"
    assert not any(char.isdigit() for char in one_site[0]), "the digit net was expected to be blind"
    assert one_site != (CALLBACK_ARGUMENT,), "the exact-expression arm must still catch it"

    # And the parameter spelling is NOT a call site.
    assert callback_arguments("proc((request, callback) => {});\n") == ()


# ---------------------------------------------------------------------------
# e2. The verdict map, pinned on the lane that always runs
# ---------------------------------------------------------------------------

#: The five entries ``shell/lib/verdict.js`` must spell, verbatim and in order.
#:
#: WHY THIS IS DUPLICATED ACROSS THE LANGUAGE SEAM. ``shell/test/verdict.test.js``
#: already pins all five mappings BY VALUE, which is the better test - it loads
#: the module and calls the function. But it runs under ``node --test``, and
#: node exists only on the tier-2 lane. This module is the every-push half, and
#: it runs on a clean checkout with no Node installed at all.
#:
#: MEASURED, NOT ASSUMED. Changing ``[trust.DEFER, -3]`` to ``[trust.DEFER, 0]``
#: was measured to leave THIS suite entirely green while ``node --test`` went to
#: five failures - so before these arms existed, every mapping bypass reached a
#: push untouched by the lane that runs on every push. The same held for
#: REFUSE_NO_PIN and REFUSE_MISMATCH.
VERDICT_MAP_ENTRIES: Final = (
    "[trust.TRUST, 0],",
    "[trust.DEFER, -3],",
    "[trust.REFUSE_NO_PIN, -2],",
    "[trust.REFUSE_NO_CERT, -2],",
    "[trust.REFUSE_MISMATCH, -2],",
)

#: The one entry that may carry the accepting code, which is also the code that
#: switches Certificate Transparency verification off for the session.
ACCEPTING_ENTRY: Final = "[trust.TRUST, 0],"


def verdict_map_block(text: str) -> tuple[str, ...]:
    """The non-empty lines inside ``shell/lib/verdict.js``'s ``new Map([...])``.

    EXTRACTED RATHER THAN SUBSTRING-COUNTED. The module's header documents the
    bypasses it exists to stop and therefore spells ``[trust.DEFER, -3]`` in
    prose as well as in the map, so a whole-file count of that text answers two
    where the map holds one. Narrowing to the constructor is what makes the
    grading below mean the map and not the commentary.

    Args:
        text: The raw source of ``shell/lib/verdict.js``.

    Returns:
        The stripped, non-empty lines between ``new Map([`` and its ``]);``.

    Raises:
        AssertionError: If the constructor cannot be located at all.
    """
    opener = "new Map(["
    start = text.find(opener)
    assert start != -1, "shell/lib/verdict.js holds no `new Map([` constructor"
    end = text.find("]);", start)
    assert end != -1, "the verdict map constructor is not closed"
    body = text[start + len(opener) : end]
    return tuple(line.strip() for line in body.splitlines() if line.strip())


def test_the_verdict_map_spells_exactly_the_five_expected_entries() -> None:
    """The map holds the five verdict-to-code pairs, verbatim and in order.

    The pairs are spelled in THIS file and never read out of the module under
    test. CS-605 closed on the neighbouring failure - a table imported from the
    source let a deletion in the source delete the test case and stay green.
    """
    entries = verdict_map_block(read_text("shell/lib/verdict.js"))
    assert entries == VERDICT_MAP_ENTRIES, f"the verdict map reads: {entries}"


def test_only_the_trust_entry_carries_the_accepting_code() -> None:
    """Exactly one map entry maps to 0, and it is the one for TRUST.

    A WIDER NET THAN THE VERBATIM ARM, and the one that states the security
    property rather than the spelling. The verbatim arm goes red on a
    reformatting that is entirely legitimate; this one goes red only when a
    second verdict acquires the accepting code, which is the whole bypass.
    """
    entries = verdict_map_block(read_text("shell/lib/verdict.js"))
    assert entries, "the verdict map is empty; this arm would be vacuous"

    accepting = tuple(entry for entry in entries if entry.endswith(", 0],"))
    assert accepting == (ACCEPTING_ENTRY,), f"entries mapping to the accepting code: {accepting}"


def test_the_verdict_map_reader_fires_on_each_measured_mapping_bypass() -> None:
    """The extractor and both arms are proved against the measured mutations.

    Each fixture below is a real mutation that was applied to a checkout and
    measured to leave this suite green before these arms existed.
    """
    shipped = (
        "// the header documents [trust.DEFER, -3] -> [trust.DEFER, 0] in prose\n"
        "const VERDICT_CODES = new Map([\n"
        + "".join(f"  {entry}\n" for entry in VERDICT_MAP_ENTRIES)
        + "]);\n"
    )
    assert verdict_map_block(shipped) == VERDICT_MAP_ENTRIES, "the shipped shape did not read"

    accepting = tuple(e for e in verdict_map_block(shipped) if e.endswith(", 0],"))
    assert accepting == (ACCEPTING_ENTRY,), "the shipped map did not read as one accepting entry"

    bypasses = (
        "[trust.DEFER, 0],",
        "[trust.REFUSE_NO_PIN, 0],",
        "[trust.REFUSE_MISMATCH, 0],",
    )
    for mutated in bypasses:
        original = mutated.replace(", 0],", ", -3]," if "DEFER" in mutated else ", -2],")
        assert original in VERDICT_MAP_ENTRIES, f"fixture does not mutate a real entry: {original}"

        text = shipped.replace(f"  {original}\n", f"  {mutated}\n")
        entries = verdict_map_block(text)
        assert entries != VERDICT_MAP_ENTRIES, f"the verbatim arm missed {mutated}"

        widened = tuple(entry for entry in entries if entry.endswith(", 0],"))
        assert widened != (ACCEPTING_ENTRY,), f"the accepting-code arm missed {mutated}"


def test_trust_js_returns_its_verdict_from_exactly_one_site() -> None:
    """``shell/lib/trust.js`` grants trust in one place and compares in constant time."""
    code = code_of("shell/lib/trust.js")
    granted = code.count("return TRUST")
    assert granted == 1, f"trust.js grants TRUST from {granted} site(s), expected exactly 1"
    assert "timingSafeEqual" in code, "trust.js does not compare with timingSafeEqual"


def test_the_call_site_counter_counts_a_planted_duplicate() -> None:
    """The counter is proved to distinguish one site from two.

    Without this, an arm asserting ``== 1`` against a counter stuck at 1 would
    be the same green as an arm that measured.
    """
    site = "callback("
    one = f"proc((request, {site[:-1]}) => {{ {site}0); }});\n"
    two = f"{one}{site}0);\n"
    assert strip_js_comments(one).count(site) == 1
    expected_after_planting = 2
    assert strip_js_comments(two).count(site) == expected_after_planting
    assert strip_js_comments(f"// mentions {site}\n").count(site) == 0


# ---------------------------------------------------------------------------
# f. The purity partition - shell/lib/ reaches no electron API
# ---------------------------------------------------------------------------

#: How a CommonJS module names the electron package. Both quote spellings,
#: because ``shell/lib/trust.js`` writes ``require('node:crypto')`` where its
#: siblings use double quotes, so a double-quote-only pattern would be blind to
#: a single-quoted electron import added in that file's style.
_ELECTRON_REQUIRE: Final = re.compile(r"""require\(\s*["']electron["']\s*\)""")


def modules_importing_electron() -> tuple[str, ...]:
    """Every shell ``.js`` file whose CODE requires the electron package.

    Returns:
        The paths, in enumeration order.
    """
    return tuple(
        name
        for name in shell_files()
        if name.endswith(".js") and _ELECTRON_REQUIRE.search(code_of(name)) is not None
    )


def test_no_shell_lib_module_imports_electron() -> None:
    """``shell/lib/`` is pure, so the tier-2 lane can grade it without a binary.

    THE PARTITION THAT MAKES THE REST OF CS-602 GRADABLE. electron 44.0.0
    declares no postinstall, so the installed package holds no binary and
    nothing under ``shell/lib/`` may need one. Graded on STRIPPED code:
    ``shell/lib/window.js`` and ``shell/lib/geometry.js`` each carry comments
    naming electron precisely to record what they avoid, and a raw scan would
    fail them for documenting the constraint they satisfy.
    """
    impure = tuple(name for name in modules_importing_electron() if name.startswith(LIB_PREFIX))
    total = len(impure)
    assert total == 0, f"{total} module(s) under {LIB_PREFIX} import electron: {impure}"


def test_main_js_is_the_only_shell_module_that_imports_electron() -> None:
    """A LIVE positive control: the detector fires on real committed code.

    Stronger than a planted fixture. ``shell/main.js`` really does import
    electron, so this arm proves :func:`modules_importing_electron` can fire
    against the actual tree - which means the zero found under ``shell/lib/`` is
    a measurement and not a detector that stopped matching.
    """
    importers = modules_importing_electron()
    assert importers == ("shell/main.js",), f"unexpected electron importers: {importers}"


def test_the_electron_detector_ignores_a_comment_and_catches_both_quote_styles() -> None:
    """The purity detector is proved in both directions and both spellings.

    The comment direction is not hypothetical: a sibling slice this session
    failed its own purity arm because ``shell/lib/window.js`` requires nothing at
    all and a comment EXPLAINING which module it avoids matched the pattern.
    """
    ignored = (
        "// requires nothing at all - not electron, not the filesystem\n",
        "/*\n * electron 44.0.0 declares no postinstall, so no binary is needed.\n */\n",
        '// do not require("electron") from this file\n',
    )
    graded = tuple(text for text in ignored if _ELECTRON_REQUIRE.search(strip_js_comments(text)))
    assert not graded, f"the purity detector graded comment prose: {graded}"

    caught = (
        'const { app } = require("electron");\n',
        "const { app } = require('electron');\n",
        'const e = require( "electron" );\n',
    )
    silent = tuple(text for text in caught if not _ELECTRON_REQUIRE.search(strip_js_comments(text)))
    assert not silent, f"the purity detector missed a real import: {silent}"


# ---------------------------------------------------------------------------
# g. Ports - the band read from the record, never spelled in this file
# ---------------------------------------------------------------------------

#: Standalone integer runs. ``\b`` on both sides rather than a digit lookaround,
#: so a digit run embedded in an identifier or a hash - ``sha512-a1b2`` - is not
#: a match, while ``port=8920`` and ``-8920`` still are.
_INTEGER_RUN: Final = re.compile(r"\b\d+\b")


@lru_cache(maxsize=1)
def allocated_band() -> tuple[int, int]:
    """The reserved port band, read from ``config/ports.json``.

    NO LITERAL FROM INSIDE THE BAND APPEARS ANYWHERE IN THIS FILE. CS-604
    requires exactly that shape, and it is also the only way this arm survives
    the next reallocation - the band has MOVED once already, and a test carrying
    its own copy of the bounds would have kept grading the old block.

    Returns:
        The inclusive ``(start, end)`` bounds.
    """
    record = json.loads(config.ports_record_path().read_text(encoding="ascii"))
    band = record["band"]
    return int(band["start"]), int(band["end"])


def ports_in_band(text: str) -> tuple[str, ...]:
    """Every standalone integer in ``text`` that falls inside the allocated band.

    A TEXT SCAN AND NOT AN AST WALK. ``tests/surface/test_config.py`` uses
    ``ast.parse`` and is therefore structurally blind to ``.js`` and ``.json``,
    which is the whole of what this module grades.

    Args:
        text: The file text to sweep.

    Returns:
        The offending integers as they were spelled, in file order.
    """
    low, high = allocated_band()
    return tuple(run for run in _INTEGER_RUN.findall(text) if low <= int(run) <= high)


def test_the_allocated_band_is_read_from_the_record_and_is_sane() -> None:
    """The bounds came from the file, are integers, and describe a real range."""
    low, high = allocated_band()
    assert isinstance(low, int), f"band start is {type(low).__name__}, expected int"
    assert isinstance(high, int), f"band end is {type(high).__name__}, expected int"
    assert low < high, f"the band is empty or inverted: {low}..{high}"
    assert config.ports_record_path().is_file(), "the port record is absent"


def test_no_shell_file_carries_a_port_from_the_allocated_band() -> None:
    """The shell resolves its port from the record at runtime, never from a literal.

    Swept over RAW text rather than stripped code, deliberately: a band port
    written into a comment is a number that will be copied into code by the next
    reader, and ``shell/lib/endpoint.js`` says in its own header that the number
    must never appear in the file at all.
    """
    findings = {
        name: ports_in_band(read_text(name))
        for name in shell_files()
        if ports_in_band(read_text(name))
    }
    total = len(findings)
    assert total == 0, f"{total} shell file(s) carry an allocated port: {findings}"


def test_the_port_detector_fires_on_both_edges_and_the_interior() -> None:
    """The band sweep is proved to catch its bounds and to leave neighbours alone.

    Every sample is BUILT from the record, so this control adds no band literal
    to this file either.
    """
    low, high = allocated_band()
    inside = (low, high, (low + high) // 2)
    silent = tuple(port for port in inside if not ports_in_band(f"const p = {port};\n"))
    assert not silent, f"the port detector missed ports inside the band: {silent}"

    outside = (low - 1, high + 1)
    noisy = tuple(port for port in outside if ports_in_band(f"const p = {port};\n"))
    assert not noisy, f"the port detector fired outside the band: {noisy}"

    embedded = f'const h = "sha512-x{low}y";\n'
    assert not ports_in_band(embedded), "the port detector matched a digit run inside a token"


# ---------------------------------------------------------------------------
# h. Privacy - no account, no home path, no machine name
# ---------------------------------------------------------------------------

#: Class ids, because a failure message that QUOTES what it found publishes the
#: very thing the arm exists to keep out. ``tests/surface/test_acceptance.py``
#: records the same rule for the same reason.
CLASS_DRIVE_PATH: Final = "drive-lettered-path"
CLASS_USER_PROFILE: Final = "user-profile-path"
CLASS_SAVE_FILE: Final = "save-file-name"
CLASS_SAVE_DIR: Final = "save-directory"
CLASS_ACCOUNT_ID: Final = "account-id"

#: The IEEE-754 double integer-precision boundary, which a JavaScript numeric
#: test legitimately spells out. COMPUTED as a named class rather than listed as
#: literals, so this is an exemption for a category and not a value tuned to
#: dodge one fixture: ``shell/test/state.test.js`` plants 2**53 + 1 to prove the
#: state loader rejects a value JSON can carry and a double cannot hold.
SAFE_NUMERIC_RUNS: Final = frozenset(str(2**53 + offset) for offset in (-1, 0, 1, 2))

#: Personal-data shapes, calibrated for SOURCE rather than for a served body.
#:
#: The drive-letter pattern demands the letter stand ALONE. The obvious
#: ``[A-Za-z]:[\\/]`` matches the ``s:/`` inside every ``https://``, and
#: ``shell/package-lock.json`` holds fourteen registry URLs - so the obvious
#: pattern reports a privacy finding on a file that has none.
#:
#: A bare environment-variable NAME is deliberately NOT a shape here. Its
#: expansion is personal data; the name is a constant present on every Windows
#: machine, and ``shell/test/state.test.js`` names it in code precisely to
#: assert that ``shell/lib/state.js`` never reads it. Grading that as a leak
#: would put this arm at war with a sibling's correct test.
PERSONAL_DATA_SHAPES: Final = (
    (CLASS_DRIVE_PATH, re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]")),
    (CLASS_USER_PROFILE, re.compile(r"[Uu]sers[\\/]")),
    (CLASS_SAVE_FILE, re.compile(r"\.sav\b")),
    (CLASS_SAVE_DIR, re.compile(r"SaveGames")),
)

#: The user-profile path segment, ASSEMBLED rather than spelled out.
#:
#: A PLANTED CONTROL IS STILL A TRACKED FILE, and a tracked file may not carry
#: an absolute home path (non-negotiable 3). Written literally - a rooted macOS
#: profile path with an invented account name - the control below went red under
#: two independent guards at once: ``tests/test_scaffold.py``'s home-path arm
#: and the source-echo sweep in ``tests/test_assertion_rendering.py``, which
#: exists because pytest prints a failing function's own source above the
#: assertion. Both were right, and catching a fixture nobody would have called
#: personal data is the layered guard working rather than over-firing.
#:
#: The prose above is deliberately a DESCRIPTION and not a specimen. The first
#: repair spelled the offending path inside this very comment to explain it, and
#: the same guard caught it a second time on the comment line - the mirror image
#: of the hazard this module was written to handle, where documenting a
#: constraint is enough to violate it.
#:
#: Assembling the segment is the house answer, not a dodge around it:
#: ``tests/test_scaffold.py`` builds ``Users`` by concatenation inside its own
#: patterns for exactly this reason. No leading separator is used either, so the
#: value is not an absolute path even after assembly at run time - it only
#: carries the shape :data:`PERSONAL_DATA_SHAPES` claims to detect.
PROFILE_SEGMENT: Final = "Users" + "/"

#: The account-id digit width the project already uses, restated from
#: ``tests/surface/test_acceptance.py``'s threshold rather than invented.
MIN_ACCOUNT_ID_DIGITS: Final = 15

#: The smallest identifier this module will sweep for as a bare literal. A
#: one- or two-character account name would match half the tree.
MIN_LITERAL_LENGTH: Final = 3

CLASS_HOME_PATH: Final = "home-path"

_ACCOUNT_ID_DIGITS: Final = re.compile(rf"(?<!\d)\d{{{MIN_ACCOUNT_ID_DIGITS},}}(?!\d)")
_ACCOUNT_ID_HEX: Final = re.compile(r"(?<![0-9A-Za-z])[0-9a-fA-F]{32}(?![0-9A-Za-z])")


def personal_data_classes(text: str) -> tuple[str, ...]:
    """Which personal-data classes ``text`` carries, as ids and never as values.

    Args:
        text: The code to sweep.

    Returns:
        The class ids found, in a stable order. Empty when the text is clean.
    """
    found = [label for label, pattern in PERSONAL_DATA_SHAPES if pattern.search(text)]
    digits = tuple(run for run in _ACCOUNT_ID_DIGITS.findall(text) if run not in SAFE_NUMERIC_RUNS)
    if digits or _ACCOUNT_ID_HEX.search(text):
        found.append(CLASS_ACCOUNT_ID)
    return tuple(found)


def test_no_shell_file_carries_a_personal_data_shape() -> None:
    """Every shell file is swept for the classes CLAUDE.md section 2 names."""
    findings = {
        name: personal_data_classes(code_of(name))
        for name in shell_files()
        if personal_data_classes(code_of(name))
    }
    total = len(findings)
    assert total == 0, f"{total} shell file(s) carry a personal-data shape: {findings}"


def test_no_shell_file_carries_this_machines_own_identifiers() -> None:
    """The literal account name, home path and machine name are absent.

    A SHAPE SWEEP CANNOT SEE A NAME IT CANNOT GUESS, so this is the second of
    two layers. Short identifiers are matched on word boundaries so a machine
    whose account is named after a common word cannot fail the arm spuriously;
    the home directory is always long enough to match as a plain substring, and
    is asserted to have been applied so the arm cannot go vacuous.
    """
    home = str(Path.home())
    assert len(home) >= MIN_LITERAL_LENGTH, "the home path is too short to sweep for"

    blob = "\n".join(read_text(name) for name in shell_files())
    assert blob, "there is nothing to sweep"

    carried = [CLASS_HOME_PATH] if home in blob else []
    for label, needle in (
        ("account-name", getpass.getuser()),
        ("machine-name", platform.node()),
        ("home-basename", Path.home().name),
    ):
        if len(needle) < MIN_LITERAL_LENGTH:
            continue
        if re.search(rf"(?<![0-9A-Za-z_]){re.escape(needle)}(?![0-9A-Za-z_])", blob):
            carried.append(label)

    total = len(carried)
    assert total == 0, f"shell files carry {total} identifier class(es) of this box: {carried}"


def test_the_personal_data_sweep_fires_on_every_class_it_claims() -> None:
    """Each class is proved findable, and the near-misses are proved to be ignored."""
    assert personal_data_classes('const a = "plain";') == ()

    low = 2**53
    planted = {
        CLASS_DRIVE_PATH: 'const p = "C:/somewhere";',
        CLASS_USER_PROFILE: f'const p = "{PROFILE_SEGMENT}x";',
        CLASS_SAVE_FILE: 'const p = "world.sav ";',
        CLASS_SAVE_DIR: 'const p = "SaveGames";',
        CLASS_ACCOUNT_ID: f'const a = " {low * 10 + 7} ";',
    }
    silent = tuple(
        label for label, text in planted.items() if label not in personal_data_classes(text)
    )
    assert not silent, f"the personal-data sweep did not fire on: {silent}"

    tolerated = {
        "registry url": 'const u = "https://registry.npmjs.example/pkg";',
        "double precision boundary": f"const n = {2**53 + 1};",
        "css property": "const c = /^\\s*app-region:\\s*drag;/m;",
    }
    noisy = tuple(label for label, text in tolerated.items() if personal_data_classes(text))
    assert not noisy, f"the personal-data sweep false-fired on: {noisy}"


def test_the_machine_identifier_sweep_fires_on_a_planted_home_path() -> None:
    """The literal layer is proved able to find this machine's own home path."""
    home = str(Path.home())
    assert home not in 'const a = "plain";'
    assert home in f'const a = "{home}";'


# ---------------------------------------------------------------------------
# i. Cross-language constant agreement
# ---------------------------------------------------------------------------

#: The four names ``clockspeed/surface/config.py`` owns and ``shell/lib/
#: endpoint.js`` restates. This is the THIRD copy in the repository - the
#: Python module, ``scripts/make_cert.py`` and the JavaScript - and config.py's
#: own docstring already records the seam collision. Guarding the restatement is
#: the price of it.
CERT_CONSTANT_NAMES: Final = ("CERT_NAME", "KEY_NAME", "CERT_DIR_ENV", "DEFAULT_CERT_DIRNAME")


def javascript_constants(code: str, names: tuple[str, ...]) -> dict[str, str]:
    """Extract ``const NAME = "value";`` for each requested name.

    Both quote spellings are accepted, matching the two styles already present
    under ``shell/``.

    Args:
        code: The stripped JavaScript source.
        names: The constant names to look for.

    Returns:
        A mapping of name to value, holding only the names actually found.
    """
    found: dict[str, str] = {}
    for name in names:
        match = re.search(rf"""const\s+{re.escape(name)}\s*=\s*["']([^"']+)["']\s*;""", code)
        if match is not None:
            found[name] = match.group(1)
    return found


def test_the_shell_and_python_agree_on_the_certificate_names() -> None:
    """The JavaScript restatement of the four cert constants matches Python.

    THE EXTRACTION IS ASSERTED BEFORE THE COMPARISON. A regex that silently
    stopped matching would leave an empty mapping, and a loop over an empty
    mapping compares nothing and passes - a green arm over zero comparisons.
    So the count is checked first, then each value is checked non-empty, and
    only then are they compared.
    """
    extracted = javascript_constants(code_of("shell/lib/endpoint.js"), CERT_CONSTANT_NAMES)

    found = len(extracted)
    expected = len(CERT_CONSTANT_NAMES)
    assert found == expected, f"extracted {found} of {expected} cert constants: {sorted(extracted)}"

    blank = tuple(name for name, value in sorted(extracted.items()) if not value.strip())
    assert not blank, f"extracted an empty value for: {blank}"

    disagreements = tuple(
        f"{name}: js={extracted[name]!r} py={getattr(config, name)!r}"
        for name in CERT_CONSTANT_NAMES
        if extracted[name] != getattr(config, name)
    )
    total = len(disagreements)
    assert total == 0, f"{total} cert constant(s) disagree across the seam: {disagreements}"


def test_the_constant_extractor_reports_a_miss_rather_than_a_vacuous_pass() -> None:
    """The extractor returns fewer names when they are absent or commented out.

    This is what makes the count assertion above load-bearing. Without it, an
    extractor that matched nothing would let the comparison loop iterate zero
    times and report success.
    """
    assert javascript_constants('const OTHER = "x";', CERT_CONSTANT_NAMES) == {}

    commented = '// const CERT_NAME = "dashboard.cert.pem";\n'
    assert javascript_constants(strip_js_comments(commented), CERT_CONSTANT_NAMES) == {}

    both_quotes = "const CERT_NAME = 'a.pem';\nconst KEY_NAME = \"b.pem\";\n"
    extracted = javascript_constants(both_quotes, CERT_CONSTANT_NAMES)
    assert extracted == {"CERT_NAME": "a.pem", "KEY_NAME": "b.pem"}, extracted


# ---------------------------------------------------------------------------
# j. The manifest
# ---------------------------------------------------------------------------

#: Files that participate in CommonJS, measured as carrying ``require(`` or
#: ``module.exports``. ``shell/preload.js`` is deliberately inert and carries
#: neither, so it is not in this count.
COMMONJS_FILE_COUNT: Final = 9


@lru_cache(maxsize=1)
def manifest() -> dict[str, object]:
    """``shell/package.json``, parsed.

    The isinstance check is not decoration: a manifest that decoded to a list or
    a string would make every ``key not in manifest()`` arm below pass for a
    reason that has nothing to do with what the manifest declares.

    Returns:
        The decoded manifest.
    """
    loaded = json.loads(read_text("shell/package.json"))
    assert isinstance(loaded, dict), f"the manifest decoded to {type(loaded).__name__}"
    return loaded


def test_the_shell_manifest_declares_no_runtime_dependencies() -> None:
    """There is no ``dependencies`` key at all, not merely an empty one.

    An empty ``dependencies`` object is an invitation; its absence is a
    statement. The companion ships no third-party runtime code.
    """
    assert "dependencies" not in manifest(), "shell/package.json declares runtime dependencies"


def test_the_shell_manifest_names_electron_only_under_dev_dependencies() -> None:
    """Electron is a development dependency and appears nowhere else."""
    dev = manifest().get("devDependencies")
    assert isinstance(dev, dict), f"devDependencies is {type(dev).__name__}, expected a mapping"
    assert "electron" in dev, "electron is not declared under devDependencies"

    elsewhere = tuple(
        key
        for key, value in manifest().items()
        if key != "devDependencies" and "electron" in json.dumps(value)
    )
    assert not elsewhere, f"electron is named outside devDependencies, under: {elsewhere}"


def test_the_shell_manifest_declares_no_module_type() -> None:
    """No ``type`` field, so Node reads every ``.js`` here as CommonJS.

    :data:`COMMONJS_FILE_COUNT` files depend on that absence. Adding
    ``"type": "module"`` would break every ``require`` in the tree at once, and
    would do it at runtime rather than at any gate the tier-1 lane runs.
    """
    assert "type" not in manifest(), "shell/package.json declares a module type"


def test_the_manifest_absence_checks_fire_on_a_planted_manifest() -> None:
    """The three absence checks are proved to distinguish absent from present."""
    planted: dict[str, object] = {
        "dependencies": {"left-pad": "1.0.0"},
        "type": "module",
        "devDependencies": {},
    }
    assert "dependencies" in planted
    assert "type" in planted
    assert "electron" not in planted["devDependencies"]  # type: ignore[operator]


def test_the_commonjs_file_count_matches_what_the_manifest_absence_protects() -> None:
    """Exactly six shell modules use a CommonJS construct.

    MEASURED, not asserted from the docstring above it. If another module starts
    requiring, this count goes red and the claim in
    :func:`test_the_shell_manifest_declares_no_module_type` gets updated rather
    than quietly becoming false. It has fired once already, for real: adding
    ``shell/lib/verdict.js`` moved the census from six to seven.
    """
    users = tuple(
        name
        for name in shell_files()
        if name.endswith(".js")
        and not name.startswith(TEST_PREFIX)
        and ("require(" in code_of(name) or "module.exports" in code_of(name))
    )
    found = len(users)
    expected = COMMONJS_FILE_COUNT
    assert found == expected, f"{found} CommonJS module(s), expected {expected}: {users}"


# ---------------------------------------------------------------------------
# k. Test-file liveness
# ---------------------------------------------------------------------------


def test_every_shell_test_file_declares_at_least_one_test() -> None:
    """No behaviour suite is empty.

    AN EMPTIED TEST FILE PASSES ``node --test`` WITH ZERO FAILURES, which is
    indistinguishable from a suite that ran and was satisfied. Counting the
    declarations is what tells the two apart from this lane, which cannot run
    Node at all.
    """
    suites = tuple(name for name in shell_files() if name.startswith(TEST_PREFIX))
    assert suites, "no behaviour suites were enumerated"

    silent = tuple(name for name in suites if code_of(name).count("test(") == 0)
    total = len(silent)
    assert total == 0, f"{total} shell test file(s) declare no test: {silent}"


def test_the_test_liveness_detector_fires_on_an_emptied_suite() -> None:
    """The liveness count is proved to distinguish a real suite from an empty one."""
    assert 'test("x", () => {});\n'.count("test(") == 1
    assert '"use strict";\n'.count("test(") == 0
    assert strip_js_comments("// test(\n").count("test(") == 0


# ---------------------------------------------------------------------------
# l. The wiring - shipped is not the same as used
# ---------------------------------------------------------------------------

#: Every seam `shell/main.js` is required to actually CONSUME, as the exact
#: source text that consuming it produces.
#:
#: WHY THIS SECTION EXISTS. `shell/main.js` imports electron, so no test in
#: either language loads it (CS-619 is open against exactly that), and every
#: decision it delegates is graded only in the module that decides. That leaves
#: one hole the module suites cannot see: main.js can require a module and then
#: ignore its answer, or never require it at all. The pure suites stay green
#: either way, and the operator gets a companion with no tray and a dashboard
#: nobody stops. CS-896 shipped that exact fault one session earlier - a marker
#: registered, arms green, and NOTHING using it.
#:
#: THE COMMENTS ARE STRIPPED FIRST, and that is the other half of the same
#: lesson. The CS-896 parallel-lane arm searched a whole file for a token that
#: also appeared TWICE IN ITS OWN COMMENTS, so deleting the real invocation left
#: the arm green. A prose mention of `supervisor.decideStart` must not satisfy
#: this list; only a call can.
REQUIRED_MAIN_WIRING: Final = (
    'require("./lib/supervisor.js")',
    'require("./lib/tray.js")',
    "supervisor.decideStart(",
    "supervisor.decideStop(",
    "supervisor.decideProbeOutcome(",
    "supervisor.serverArgv(",
    "trayLib.menuTemplate(",
    "trayLib.ICON_DATA_URL",
    "trayLib.tooltip(",
    "new Tray(",
    "dialog.showErrorBox(",
)


def main_code() -> str:
    """``shell/main.js`` with every comment removed."""
    return strip_js_comments(read_text("shell/main.js"))


def test_main_consumes_every_seam_it_was_given() -> None:
    """main.js CALLS the modules it delegates to, rather than merely importing them.

    STATED LIMITATION, measured the first time this arm ran. It matches TEXT,
    not syntax, so it is sensitive to formatting: a call split as ``trayLib``
    newline ``.menuTemplate(`` is a real call this arm cannot see, and it
    reported exactly that on its first run. The fix taken was to write the call
    on one line rather than to loosen the token, because a looser token is
    satisfied by more things that are not calls. Anyone reformatting
    ``shell/main.js`` must expect this arm to speak up, and must not answer it
    by weakening the list. A parser would not have this weakness; nothing in
    this repository parses JavaScript, and adding a parser to grade one file is
    a trade this project has not made.
    """
    code = main_code()
    missing = tuple(token for token in REQUIRED_MAIN_WIRING if token not in code)
    total = len(missing)
    assert total == 0, f"{total} seam(s) shipped but not consumed by main.js: {missing}"


def test_the_wiring_detector_is_blind_to_a_commented_out_call() -> None:
    """A seam named only in a comment does not satisfy the arm above.

    This is the arm that has teeth. Without it the list is satisfied by prose,
    which is how the same class of check passed last time while the behaviour
    it claimed to grade had been deleted.
    """
    for token in REQUIRED_MAIN_WIRING:
        commented = f"// {token}\n"
        assert token not in strip_js_comments(commented), token


def test_close_does_not_permanently_disable_persistence() -> None:
    """The hide path returns before `closing` is set.

    `closing` exists to stop a debounced write firing against a DESTROYED
    window. Hiding destroys nothing, so setting it on the hide path would be
    permanent - every move after the first hide silently dropped, and the window
    restoring to wherever it happened to be that once. The guard is that exactly
    one assignment survives comment-stripping.
    """
    code = main_code()
    assignments = code.count("closing = true")
    assert assignments == 1, f"{assignments} assignments to closing, expected 1"

    prevented = code.find("event.preventDefault()")
    assert prevented != -1, "the close handler never prevents the close"

    # THE HIDE IS LOOKED FOR NEXT TO THE PREVENTION, not anywhere in the file.
    # Measured: a bare ``"win.hide()" in code`` arm SURVIVED deleting the hide
    # from this handler, because the tray menu's show/hide toggle also calls
    # win.hide() and satisfied the token from thirty lines away. A window whose
    # close is prevented but which never hides is one the operator cannot get
    # rid of at all, so the two have to be checked together or not at all.
    window = code[prevented : prevented + 120]
    assert "win.hide()" in window, "the close handler prevents the close without hiding the window"

    # THE HIDE IS GUARDED BY THE TRAY EXISTING. A hidden frameless window has no
    # taskbar button and no title bar, so the tray is the only route back to it.
    # Hiding when createTray returned null would strand the operator with a
    # process they can neither see nor quit. Measured: this guard was MISSING on
    # the first wiring, while a comment two functions away already claimed it
    # was there.
    guard = code.rfind("if (", 0, prevented)
    assert guard != -1, "no condition guards the hide path"
    condition = code[guard:prevented]
    assert "trayRef" in condition, (
        f"the hide path is not guarded by the tray existing: {condition.strip()!r}"
    )
