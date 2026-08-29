"""CS-601 slice S5 - the dashboard's three static assets, graded at rest.

WHAT THIS MODULE GRADES, AND WHAT IT DOES NOT. Every arm here reads the three
shipped asset files as BYTES off disk and asserts a property of what a human
typed. That is a STATIC control. CONVENTIONS.md section 13.3 requires asserting
COMPUTED styles, which needs a real browser laying the page out, and nothing in
this file does that. The CS-600 five-phase visual audit run against a screenshot
of ``tests/surface/audit_harness.py`` is what discharges 13.3; the arms below
are the at-rest half and are reported as exactly that.

WHY AT-REST MATTERS ANYWAY, given a Content-Security-Policy already blocks a
remote fetch at runtime. ``clockspeed/surface/server.py`` sends
``default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'``,
so a CDN font reference would fail to load rather than leak. But a header is one
edit away from being relaxed and an asset that CONTAINS a remote reference is a
leak waiting for that edit. Two independent gates - the header at runtime and
these arms at rest - is the same shape ``providers.StaticAssets`` already uses
for the asset name set, and for the same reason.

EVERY DETECTOR IS A FUNCTION, AND EVERY DETECTOR HAS A PLANTED-MUTATION ARM.
A gate whose subject does not exist passes for the wrong reason - a sibling
slice this session shipped a traversal arm that was green because the target
file was absent, so ABSENCE was doing the work the gate got credit for. Each
detector below is therefore run twice: once against the real asset text, where
it must find nothing, and once against that same text with the banned
construct PLANTED, where it must find it. A detector that cannot fire is a
detector that grades nothing.
"""

from __future__ import annotations

import getpass
import http.client
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.save.header import MASK_DIGEST_CHARACTERS, MASK_PREFIX, masked_token
from clockspeed.surface import config, server
from clockspeed.surface.api import contract, health, pending, solve, world
from tests.surface import audit_harness

if TYPE_CHECKING:
    from collections.abc import Iterator

# ---------------------------------------------------------------------------
# Where the assets are, named through their owners rather than restated
# ---------------------------------------------------------------------------

#: The asset directory, read from the module that owns the answer
#: (``clockspeed/surface/config.py``) rather than rebuilt from ``__file__``.
WEB_DIR: Final = config.default_web_dir()

#: The three files, read from the server's own frozen table so this module and
#: the route table cannot disagree about which names exist.
ASSET_NAMES: Final = tuple(sorted(server.ASSET_NAMES))

INDEX: Final = "index.html"
STYLESHEET: Final = "app.css"
SCRIPT: Final = "app.js"

#: The route template ``clockspeed/surface/api/world.py`` answers. Spelled here
#: rather than imported because that module names it ``ENDPOINT``, which would
#: collide with ``health.ENDPOINT`` at any shared import site.
WORLD_ENDPOINT: Final = "/api/world"

#: The highest byte the project's character-set rule admits. Restated from
#: nowhere: it is the same 0x7E ``contract.MAX_ASCII_BYTE`` and the commit gate
#: both use, and it is spelled here because a test that imports a constant to
#: assert the constant grades nothing.
MAX_ASCII_BYTE: Final = 0x7E

#: How long a request against the loopback stand-in may take before it is a
#: failure rather than a slow machine.
SOCKET_TIMEOUT: Final = 10.0

HTTP_OK: Final = 200
HTTP_NOT_FOUND: Final = 404

#: The smallest CSS pixel box an interactive target may declare.
MIN_TARGET_PX: Final = 24

#: The reserved dashboard port band. NO LITERAL FROM INSIDE IT APPEARS ANYWHERE
#: IN THIS SLICE - the two bounds are exclusive of the band's interior in the
#: comparison below, and the band itself is named by its edges.
PORT_BAND_FIRST: Final = 8919 + 1
PORT_BAND_LAST: Final = 8940 - 1


def read_asset(name: str) -> str:
    """Read one asset as text, decoded strictly as ASCII.

    Decoding as ASCII rather than as UTF-8 is deliberate: a byte above 0x7E
    raises here instead of decoding into a character that a later arm has to
    notice. The character-set arm asserts the same thing on raw bytes, so this
    is the second of two gates rather than the only one.

    Args:
        name: A filename from :data:`ASSET_NAMES`.

    Returns:
        The file's text.
    """
    return (WEB_DIR / name).read_bytes().decode("ascii")


# ---------------------------------------------------------------------------
# a. The files exist, under the names the server will ask for
# ---------------------------------------------------------------------------


def test_the_server_names_exactly_three_assets() -> None:
    """The name set this module grades is the server's own, and holds three.

    An arm that grades a name set it invented would stay green while the server
    served a fourth file nobody checked.
    """
    expected = 3
    assert len(ASSET_NAMES) == expected, ASSET_NAMES
    assert set(ASSET_NAMES) == {INDEX, STYLESHEET, SCRIPT}, ASSET_NAMES


def test_every_named_asset_exists_on_disk() -> None:
    """Each of the three files the static table names is present and non-empty.

    THIS ARM IS THE PRECONDITION FOR EVERY OTHER ARM IN THIS FILE. Without it,
    a detector arm that read a missing file would error rather than pass, but a
    detector arm written over an EMPTY file would pass while grading nothing.
    """
    missing = tuple(name for name in ASSET_NAMES if not (WEB_DIR / name).is_file())
    assert not missing, f"assets absent from {WEB_DIR.name}: {missing}"

    empty = tuple(name for name in ASSET_NAMES if (WEB_DIR / name).stat().st_size == 0)
    assert not empty, f"assets present but empty: {empty}"


def test_the_asset_directory_is_not_a_python_package() -> None:
    """``web/`` holds assets, never importable code.

    An ``__init__.py`` here would make a directory of operator-facing markup
    reachable by ``import``, which is a seam nobody declared.
    """
    assert not (WEB_DIR / "__init__.py").exists(), "web/ must not be a package"


# ---------------------------------------------------------------------------
# b. Character set - 7-bit ASCII in every byte of all three assets
# ---------------------------------------------------------------------------


def offending_bytes(data: bytes) -> tuple[int, ...]:
    """Every byte position holding a value above :data:`MAX_ASCII_BYTE`.

    Args:
        data: The raw file bytes.

    Returns:
        The offending offsets, in order.
    """
    return tuple(index for index, value in enumerate(data) if value > MAX_ASCII_BYTE)


def test_every_asset_byte_is_seven_bit_ascii() -> None:
    """No byte of any asset sits above 0x7E (non-negotiable 4)."""
    findings: list[str] = []
    for name in ASSET_NAMES:
        offsets = offending_bytes((WEB_DIR / name).read_bytes())
        if offsets:
            findings.append(f"{name}: {len(offsets)} byte(s), first at {offsets[0]}")
    total = len(findings)
    assert total == 0, f"non-ASCII bytes in {total} asset(s): {findings}"


def test_the_character_set_detector_fires_on_a_planted_byte() -> None:
    """Planting one high byte makes :func:`offending_bytes` report it.

    Without this, an arm that found nothing and an arm that could find nothing
    would be the same green.
    """
    clean = len(offending_bytes(b"body { color: black; }"))
    planted = len(offending_bytes(b"body { color: black; } /* \xe2\x80\x94 */"))
    assert clean == 0
    assert planted > 0, "the character-set detector did not fire on a planted byte"


def test_no_asset_holds_a_carriage_return() -> None:
    """Every asset is LF-terminated, asserted on raw bytes.

    The harness's edit tools have been observed converting a tracked file to
    CRLF while git normalised the blob and reported the tree clean, so the
    working tree violated the rule invisibly. Counting the byte is the only
    check that sees it.
    """
    findings = {
        name: (WEB_DIR / name).read_bytes().count(b"\r")
        for name in ASSET_NAMES
        if (WEB_DIR / name).read_bytes().count(b"\r") > 0
    }
    total = len(findings)
    assert total == 0, f"carriage returns in {total} asset(s): {findings}"


# ---------------------------------------------------------------------------
# c. No remote resource of any kind
# ---------------------------------------------------------------------------

#: An absolute scheme, in either spelling.
_ABSOLUTE_URL = re.compile(r"https?://")

#: A protocol-relative reference. Matched only where a URL can START - after a
#: quote, an opening parenthesis or an equals sign - because a bare ``//`` in a
#: JavaScript file is a line comment and banning that would ban comments.
_PROTOCOL_RELATIVE = re.compile(r"""["'`(=]\s*//""")

#: Any ``@import`` at all. The stylesheet needs none, and a rule that admits a
#: relative import leaves a mechanism whose only future use is a remote one.
_ANY_IMPORT = re.compile(r"@import")


def remote_references(text: str) -> tuple[str, ...]:
    """Every remote-resource reference in one asset's text.

    THREE SHAPES, EACH A REAL WAY A THIRD PARTY GETS THE OPERATOR'S IP AND
    REFERER: an absolute ``http``/``https`` URL, a protocol-relative ``//host``
    reference, and a stylesheet ``@import``. "Local. Nothing is uploaded." is a
    property of the shipped bytes, not only of the response header.

    Args:
        text: The asset's text.

    Returns:
        One finding per match, in file order.
    """
    findings: list[str] = []
    for label, pattern in (
        ("absolute-url", _ABSOLUTE_URL),
        ("protocol-relative", _PROTOCOL_RELATIVE),
        ("css-import", _ANY_IMPORT),
    ):
        findings.extend(f"{label}: {match.group(0)!r}" for match in pattern.finditer(text))
    return tuple(findings)


def test_no_asset_references_a_remote_resource() -> None:
    """None of the three assets names anything off this machine."""
    findings = {
        name: remote_references(read_asset(name))
        for name in ASSET_NAMES
        if remote_references(read_asset(name))
    }
    total = len(findings)
    assert total == 0, f"remote references in {total} asset(s): {findings}"


def test_the_remote_reference_detector_fires_on_each_planted_shape() -> None:
    """Every shape :func:`remote_references` claims to catch is proved to fire.

    One planted reference per shape, each grafted onto text that is otherwise
    clean, so a shape that silently stopped matching goes red here rather than
    going quiet in the arm above.
    """
    clean = read_asset(STYLESHEET)
    assert remote_references(clean) == ()

    planted = {
        "absolute": clean + '\n.f { background: url("https://fonts.example/a.woff2"); }\n',
        "relative": clean + '\n.f { background: url("//fonts.example/a.woff2"); }\n',
        "import": clean + '\n@import url("theme.css");\n',
    }
    silent = tuple(shape for shape, text in planted.items() if not remote_references(text))
    assert not silent, f"the remote-reference detector did not fire on: {silent}"


def test_the_page_links_only_its_own_two_local_assets() -> None:
    """``index.html`` pulls in ``app.css`` and ``app.js`` and nothing else.

    Counting the tags is what makes this a claim about the WHOLE document
    rather than about the two tags that happen to be correct.
    """
    markup = read_asset(INDEX)
    hrefs = tuple(re.findall(r'href="([^"]*)"', markup))
    sources = tuple(re.findall(r'src="([^"]*)"', markup))
    assert hrefs == (STYLESHEET,), hrefs
    assert sources == (SCRIPT,), sources


# ---------------------------------------------------------------------------
# d. No markup-injection sink
# ---------------------------------------------------------------------------

#: The sinks that turn a string into markup, plus the two that turn a string
#: into code. Each is spelled as it is USED - with the leading dot, or with the
#: bracket-access quotes - so a prose mention of the bare name in a comment
#: explaining WHY the sink is absent does not read as a use of it.
_SINKS: Final = (
    ".innerHTML",
    '["innerHTML"',
    "['innerHTML'",
    ".outerHTML",
    '["outerHTML"',
    "['outerHTML'",
    ".insertAdjacentHTML",
    "document.write",
    "eval(",
    "new Function",
)


def markup_sinks(text: str) -> tuple[str, ...]:
    """Every markup- or code-injection sink used in one asset's text.

    A SPELLING-BASED CONTROL, AND IT IS REPORTED AS ONE. It reads the shipped
    characters and cannot see a sink reached through a computed property name.
    What it does cover is every spelling this project would plausibly type, and
    the planted-mutation arm proves each one fires.

    Args:
        text: The asset's text.

    Returns:
        One finding per sink present, in the order :data:`_SINKS` lists them.
    """
    return tuple(sink for sink in _SINKS if sink in text)


def test_no_asset_uses_a_markup_or_code_injection_sink() -> None:
    """Nodes are built with ``createElement`` and filled with ``textContent``.

    Two reasons, both recorded in ``app.js`` itself: a mod class path arriving
    in ``unknown_classes`` must render as TEXT and never as markup, and
    CONVENTIONS.md section 13.3 records that an innerHTML repaint destroys
    keyboard focus.
    """
    findings = {
        name: markup_sinks(read_asset(name))
        for name in ASSET_NAMES
        if markup_sinks(read_asset(name))
    }
    total = len(findings)
    assert total == 0, f"injection sinks in {total} asset(s): {findings}"


def test_the_sink_detector_fires_on_every_sink_it_claims() -> None:
    """Each member of :data:`_SINKS` is proved to make the detector fire."""
    clean = read_asset(SCRIPT)
    assert markup_sinks(clean) == ()

    silent = tuple(sink for sink in _SINKS if not markup_sinks(clean + "\n" + sink + "x)\n"))
    assert not silent, f"the sink detector did not fire on: {silent}"


def test_the_script_builds_nodes_and_fills_them_as_text() -> None:
    """The two safe primitives are in use throughout, not merely mentioned once.

    Banning the sinks proves nothing on a file that renders nothing at all, so
    this arm is what makes the ban a statement about a page that has content.

    COUNTED, AND ON THE CODE WITH COMMENTS STRIPPED. The round-two mutation
    sweep removed one ``createElement`` call and this arm stayed green, because
    an existence check is satisfied by any single surviving mention. A page that
    builds a header, a table and a list needs several of each.
    """
    code = code_only(read_asset(SCRIPT))
    minimum_calls = 3
    minimum_writes = 2
    built = code.count("createElement")
    filled = code.count("textContent")
    assert built >= minimum_calls, f"only {built} createElement call(s) in the code"
    assert filled >= minimum_writes, f"only {filled} textContent write(s) in the code"


def test_the_script_records_why_the_sinks_are_absent() -> None:
    """``app.js`` carries the two reasons in a comment, not only in this file.

    A rule whose reason lives only in the test that enforces it is a rule the
    next editor deletes.
    """
    prose = comments_only(read_asset(SCRIPT))
    assert prose, "app.js carries no block comment at all"
    assert "unknown_classes" in prose, "the comments do not name the mod-class-path reason"
    assert "13.3" in prose, "the comments do not cite CONVENTIONS.md section 13.3"


# ---------------------------------------------------------------------------
# e. No polling timer
# ---------------------------------------------------------------------------

#: Both timer primitives. CONVENTIONS.md section 13.3: "A timer-rebuilt panel
#: becomes mouse-only, invisibly." Refresh is an explicit button.
_TIMERS: Final = ("setInterval", "setTimeout")


def timers(text: str) -> tuple[str, ...]:
    """Every timer primitive used in one asset's text.

    Args:
        text: The asset's text.

    Returns:
        One finding per timer present.
    """
    return tuple(timer for timer in _TIMERS if timer in text)


def test_the_page_repaints_on_a_button_and_never_on_a_timer() -> None:
    """No asset schedules work, and the page registers a click handler."""
    findings = {name: timers(read_asset(name)) for name in ASSET_NAMES if timers(read_asset(name))}
    total = len(findings)
    assert total == 0, f"timer primitives in {total} asset(s): {findings}"

    script = read_asset(SCRIPT)
    assert 'addEventListener("click"' in script, "app.js registers no click handler"


def test_the_timer_detector_fires_on_each_planted_timer() -> None:
    """Each member of :data:`_TIMERS` is proved to make the detector fire."""
    clean = read_asset(SCRIPT)
    assert timers(clean) == ()

    silent = tuple(timer for timer in _TIMERS if not timers(clean + "\n" + timer + "(f, 1000);\n"))
    assert not silent, f"the timer detector did not fire on: {silent}"


# ---------------------------------------------------------------------------
# f. Every custom property used is declared - a STATIC PARTIAL control
# ---------------------------------------------------------------------------

_VAR_USE = re.compile(r"var\(\s*(--[A-Za-z0-9-]+)")
_VAR_DECLARE = re.compile(r"(--[A-Za-z0-9-]+)\s*:")


def undeclared_variables(css: str) -> tuple[str, ...]:
    """Every custom property read by ``var()`` that the sheet never declares.

    Args:
        css: The stylesheet text.

    Returns:
        The undeclared names, sorted, deduplicated.
    """
    used = set(_VAR_USE.findall(css))
    declared = set(_VAR_DECLARE.findall(css))
    return tuple(sorted(used - declared))


def test_every_custom_property_the_sheet_reads_is_one_it_declares() -> None:
    """A STATIC PARTIAL control, and it is reported as exactly that.

    CONVENTIONS.md section 13.3 requires asserting COMPUTED styles, which needs
    a real browser laying the page out. This arm reads characters. It catches
    the one failure a character read CAN catch - a ``var(--x)`` whose ``--x``
    was renamed or never written, which renders as an unstyled element rather
    than as an error - and it catches nothing about what the browser computes.
    The rendered CS-600 audit is what discharges 13.3. This does not.
    """
    css = read_asset(STYLESHEET)
    used = set(_VAR_USE.findall(css))
    assert used, "the stylesheet reads no custom property at all; this arm would be vacuous"

    missing = undeclared_variables(css)
    total = len(missing)
    assert total == 0, f"{total} custom propert(ies) read but never declared: {missing}"


def test_the_undeclared_variable_detector_fires_on_a_planted_read() -> None:
    """Reading a name the sheet does not declare is reported."""
    css = read_asset(STYLESHEET)
    assert undeclared_variables(css) == ()

    planted = undeclared_variables(css + "\n.f { color: var(--never-declared-anywhere); }\n")
    assert planted == ("--never-declared-anywhere",), planted


# ---------------------------------------------------------------------------
# g. Readable in both light and dark, with an explicit body background
# ---------------------------------------------------------------------------


def _block(css: str, opener: str) -> str:
    """Return the brace-balanced text of the first block whose header matches.

    Args:
        css: The stylesheet text.
        opener: The literal that starts the block, up to and including ``{``.

    Returns:
        The block body, or the empty string when the opener is absent.
    """
    start = css.find(opener)
    if start < 0:
        return ""
    cursor = start + len(opener)
    depth = 1
    while cursor < len(css) and depth:
        if css[cursor] == "{":
            depth += 1
        elif css[cursor] == "}":
            depth -= 1
        cursor += 1
    return css[start + len(opener) : cursor - 1]


def test_the_palette_is_declared_light_first_and_redefined_for_dark() -> None:
    """Every token declared on ``:root`` is redefined under the dark query.

    A token defined in only one of the two is a colour that is correct in one
    scheme and inherited-or-wrong in the other, which is exactly the failure a
    reader notices and a static sheet hides.
    """
    css = read_asset(STYLESHEET)
    light = set(_VAR_DECLARE.findall(_block(css, ":root {")))
    assert light, "no :root palette block found"

    dark_query = _block(css, "@media (prefers-color-scheme: dark) {")
    assert dark_query, "no prefers-color-scheme: dark block found"
    dark = set(_VAR_DECLARE.findall(dark_query))

    unpaired = tuple(sorted(light ^ dark))
    total = len(unpaired)
    assert total == 0, f"{total} token(s) defined in only one scheme: {unpaired}"


def test_the_body_paints_its_own_background_and_foreground() -> None:
    """``body`` sets both, so the page never borrows the host's colours."""
    body = _block(read_asset(STYLESHEET), "body {")
    assert body, "no body rule found"
    assert "background" in body, "body declares no background"
    assert "color" in body, "body declares no colour"


# ---------------------------------------------------------------------------
# h. Interactive targets: at least 24x24 CSS px, with a visible focus style
# ---------------------------------------------------------------------------

_PX = re.compile(r"(\d+)px")

#: Every element type a keyboard or a pointer can land on. The page is asserted
#: to use exactly ONE of them, which is what makes sizing that one sufficient.
_INTERACTIVE_TAGS: Final = ("<a ", "<a>", "<input", "<select", "<textarea", "<details", "<summary")


def test_the_page_offers_exactly_one_kind_of_clickable_target() -> None:
    """The only thing to CLICK is a ``button``.

    This is the arm that makes the sizing arm below a claim about the whole
    page rather than about one selector. Adding an anchor or an input without
    sizing it turns this red.

    THIS ARM USED TO ALSO BAN EVERY ``tabindex``, on the reasoning that a
    tabindex makes something focusable that this slice has not sized. The CS-600
    audit refuted the reasoning: the table scrollers have to be focusable to be
    reachable at 375px, and a scroll container is not a pointer target that a
    24x24 minimum says anything about - it is already far larger than one. The
    ban moved to :func:`test_every_tabindex_is_a_scroll_container_at_the_default`
    below, which permits exactly that case and no other.
    """
    markup = markup_only(read_asset(INDEX))
    found = tuple(tag for tag in _INTERACTIVE_TAGS if tag in markup)
    assert not found, f"interactive elements this slice does not size: {found}"
    assert "<button" in markup, "the page offers no refresh button"


def test_the_button_declares_a_target_box_of_at_least_the_minimum() -> None:
    """``button`` sets both a minimum width and a minimum height, each >= 24px."""
    rule = _block(read_asset(STYLESHEET), "button {")
    assert rule, "no button rule found"

    for axis in ("min-width", "min-height"):
        line = next((part for part in rule.split(";") if axis in part), None)
        assert line is not None, f"button declares no {axis}"
        sizes = tuple(int(value) for value in _PX.findall(line))
        assert sizes, f"button {axis} is not declared in px"
        assert min(sizes) >= MIN_TARGET_PX, f"button {axis} is {min(sizes)}px"


def test_focus_is_visible_and_is_not_removed_anywhere() -> None:
    """A ``:focus-visible`` rule paints an outline, and nothing suppresses one."""
    css = read_asset(STYLESHEET)
    rule = _block(css, ":focus-visible {")
    assert rule, "no :focus-visible rule found"
    assert "outline" in rule, ":focus-visible declares no outline"

    suppressed = tuple(
        part.strip()
        for part in css.replace("\n", " ").split(";")
        if "outline" in part and "none" in part
    )
    assert not suppressed, f"a rule removes the focus outline: {suppressed}"


# ---------------------------------------------------------------------------
# i. Wide content scrolls inside its own box, never the page
# ---------------------------------------------------------------------------


def test_the_wide_table_scrolls_inside_its_own_container() -> None:
    """The endpoint table sits in a container that owns its overflow.

    A nine-row table with six columns is the widest thing on the page. Letting
    it push the document sideways is the failure; giving its wrapper
    ``overflow-x: auto`` is the fix, and the markup has to actually use the
    wrapper for the rule to matter.
    """
    css = read_asset(STYLESHEET)
    markup = read_asset(INDEX)

    wrapper = _block(css, ".scroll-x {")
    assert "overflow-x: auto" in wrapper, ".scroll-x does not own its overflow"

    tables = markup.count("<table")
    wrapped = markup.count('class="scroll-x"')
    assert tables > 0, "there is no table for .scroll-x to wrap"
    assert wrapped == tables, f"{wrapped} wrapper(s) for {tables} table(s)"


# ---------------------------------------------------------------------------
# i2. The CS-601 visual-audit repairs (CS-600 five-phase run, BLOCKED verdict)
#
# WHAT THESE ARMS ARE AND ARE NOT. Every one below reads bytes off disk. Three
# of the faults they cover were BEHAVIOURAL - focus survival, keyboard
# reachability, whether a sticky declaration sticks - and NONE of those can be
# settled by reading a file. They were settled by driving a real Chromium
# against tests/surface/audit_harness.py during the repair slice, and each arm
# below says in its own docstring which half it holds. An arm here going green
# means the STRUCTURE that produced the measured behaviour is still in place. It
# is a regression tripwire on a fix that was verified elsewhere, and it must
# never be read as a fresh proof of the behaviour itself.
# ---------------------------------------------------------------------------

#: A CSS block comment. Stripped before any arm that means to grade DECLARATIONS
#: rather than prose - the same fault the app.js comment splitter exists for.
_CSS_COMMENT = re.compile(r"/\*[\s\S]*?\*/")

#: An HTML comment. Stripped before any arm that means to grade MARKUP.
_HTML_COMMENT = re.compile(r"<!--[\s\S]*?-->")

#: One flat ``selector { declarations }`` rule. The declaration body is brace
#: free, so an ``@media`` wrapper never matches as a whole and the rules nested
#: inside it are each found on their own.
_CSS_RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")

#: A ``font-size`` declaring an absolute length, with its unit.
_FONT_SIZE = re.compile(r"font-size:\s*([\d.]+)(rem|px)")

#: The root font size every ``rem`` in the sheet resolves against. ``body`` sets
#: 15px but ``rem`` is relative to the ROOT element, which this page never
#: restyles, so the user agent default stands. Confirmed against the live page:
#: 0.74rem computed to 11.84px, which is this number times that factor.
ROOT_FONT_PX: Final = 16.0

#: The smallest type this page permits, in CSS px. See the app.css comment on
#: ``.facts dt`` for why the floor is a floor and not a per-label judgement.
MIN_FONT_PX: Final = 12.0

#: The widest measure running prose may declare, in characters. The upper end
#: of the 45-75 band typography holds a line return reliably trackable across;
#: the page itself sets both classes at 60ch, well inside it.
MAX_MEASURE_CH: Final = 75


def css_rules(css: str) -> tuple[tuple[str, str], ...]:
    """Every flat rule in the sheet as a ``(selector, declarations)`` pair.

    Comments are stripped first and whitespace is collapsed, so an arm can match
    a declaration without depending on how the file happens to be wrapped.

    Args:
        css: The stylesheet text.

    Returns:
        One pair per rule, selectors and bodies both whitespace-normalised.
    """
    stripped = _CSS_COMMENT.sub(" ", css)
    found = []
    for selector, body in _CSS_RULE.findall(stripped):
        name = " ".join(selector.split())
        if name.startswith("@"):
            continue
        found.append((name, " ".join(body.split())))
    return tuple(found)


def markup_only(text: str) -> str:
    """The page with its HTML comments removed.

    THIS EXISTS BECAUSE AN ARM IN THIS SECTION CAUGHT ITS OWN PROSE. The
    tabindex arm counted three ``tabindex="0"`` for two scrollers: the third was
    inside the comment in index.html explaining why the two carry one. That is
    the same failure ``code_only`` was written for one section down, arriving in
    a different language - an arm that means "the markup does this" has to be
    given the markup.

    Args:
        text: The page's full text.

    Returns:
        The text with every HTML comment replaced by a space.
    """
    return _HTML_COMMENT.sub(" ", text)


def test_the_markup_stripper_removes_a_comment_and_keeps_the_element() -> None:
    """The stripper is proved to do both halves of its job.

    The sample is the shape that actually broke: an attribute named in a comment
    beside a real element carrying it.
    """
    sample = '<!-- tabindex="0" is why --><div class="scroll-x" tabindex="0"></div>'
    stripped = markup_only(sample)
    assert stripped.count('tabindex="0"') == 1, stripped
    assert "is why" not in stripped, stripped
    assert '<div class="scroll-x"' in stripped, stripped


def test_the_css_rule_splitter_finds_rules_and_drops_comments() -> None:
    """The splitter is proved to do both halves before anything relies on it.

    A rule reader that silently returned nothing would make every arm below
    vacuously green, which is the exact shape this module exists to refuse.
    """
    sample = "/* position: sticky lives here */ a { color: red; } @media (x) { b { top: 0; } }"
    rules = dict(css_rules(sample))
    assert rules["a"] == "color: red;", rules
    assert rules["b"] == "top: 0;", rules
    assert not any(selector.startswith("@") for selector in rules), rules
    assert "sticky" not in " ".join(rules.values()), rules


def test_the_repaint_never_disables_the_control_it_repaints_from() -> None:
    """No code path assigns ``disabled`` to the refresh button.

    STATIC HALF OF A BEHAVIOURAL FIX - THIS ARM CANNOT PROVE FOCUS SURVIVES.
    It proves the mechanism that destroyed focus is absent, and nothing more. A
    browser is what decides whether focus survives a repaint, and this file
    never opens one.

    WHAT WAS MEASURED, in the CS-601 repair slice, driving Chromium against
    ``tests/surface/audit_harness.py``. Before: on a genuine trusted click, with
    the repaint confirmed landed - five fetches issued and a row node held from
    before the click no longer connected to the document - the focus events read
    ``focus, focusin, blur, focusout`` on the button and ``activeElement``
    finished at ``BODY``. After: the same click, the same landed-repaint
    evidence, focus events ``focus, focusin`` only, and ``activeElement``
    finished on the button.

    THE LANDED-REPAINT EVIDENCE IS THE LOAD-BEARING PART of that measurement. A
    focus check over a repaint that did not happen measures nothing at all, and
    the first audit pass read green for exactly that reason - the automation's
    key press arrived with an empty ``key``, no activation click was synthesised,
    and focus "survived" because nothing had touched it.
    """
    code = code_only(read_asset(SCRIPT))
    assignments = re.findall(r"\.disabled\s*=", code)
    total = len(assignments)
    assert total == 0, f"{total} assignment(s) to .disabled remain in app.js"


def test_the_busy_state_is_announced_and_is_backed_by_a_real_guard() -> None:
    """``aria-disabled`` is set and removed, and a flag actually refuses re-entry.

    THE ATTRIBUTE ALONE WOULD BE A LIE. ``aria-disabled`` announces a busy state
    and blocks nothing: the control stays clickable, so without a guard a second
    press would start a second repaint over the top of the first. The two have
    to move together, and this arm fails if either goes missing.

    Behaviourally confirmed in the repair slice rather than here: three presses
    during one in-flight repaint issued 5 fetches, not 15, and the control was
    measured mid-flight as still focused, still ``tabIndex`` 0, and with
    ``disabled`` false.
    """
    code = code_only(read_asset(SCRIPT))
    assert 'setAttribute("aria-disabled", "true")' in code, "the busy state is never announced"
    assert 'removeAttribute("aria-disabled")' in code, "the busy state is never withdrawn"

    guard = re.search(r"if\s*\(\s*(\w+)\s*\)\s*\{\s*return;", code)
    assert guard is not None, "no early return guards a second repaint"
    flag = guard.group(1)
    assert re.search(rf"\b{flag}\s*=\s*true\b", code), f"{flag} is never raised"
    assert re.search(rf"\b{flag}\s*=\s*false\b", code), f"{flag} is never lowered"


def test_a_failed_repaint_still_gives_the_control_back() -> None:
    """The busy state is released from a ``finally``, not from the happy path.

    A repaint that throws once is a bad repaint. A repaint that throws once and
    then latches the guard forever is a dead page, recoverable only by reload.
    """
    code = code_only(read_asset(SCRIPT))
    tail = code[code.find("async function refresh()") :]
    assert tail, "refresh() is not where this arm expects it"
    finally_at = tail.find("} finally {")
    assert finally_at > 0, "refresh() releases its busy state outside a finally"
    release = tail[finally_at:]
    withdrawn = 'removeAttribute("aria-disabled")' in release
    assert withdrawn, "aria-disabled is not withdrawn in finally"
    assert re.search(r"\w+\s*=\s*false", release), "the re-entry flag is not lowered in finally"


def test_every_tabindex_is_a_scroll_container_at_the_default() -> None:
    """Every ``tabindex`` on the page is ``0``, and every one is on a scroller.

    MUST-FIX 2 OF THE CS-600 AUDIT. At 375px the right-hand table columns are
    reachable only by scrolling ``.scroll-x``, which holds no link, no control
    and no focusable descendant of any kind. Whether a user agent makes a bare
    overflow container focusable is a Chromium decision that has moved between
    releases, and the companion shell ships whichever Chromium it ships.

    ``tabindex="0"`` KEEPS THE DOCUMENT ORDER; a positive value invents a second
    ordering that disagrees with the visual one, so it is banned outright here.

    Behaviourally confirmed in the repair slice rather than here: a genuine
    trusted Tab moved focus onto the scroller, which reported its accessible
    name, matched ``:focus-visible``, and painted ``solid 3px`` at ``2px``
    offset with its own 8px radius, measured 8.95:1 against the panel in dark.
    """
    markup = markup_only(read_asset(INDEX))
    values = re.findall(r'tabindex="(-?\d+)"', markup)
    assert values, "no tabindex on the page at all"
    wrong = tuple(value for value in values if value != "0")
    assert not wrong, f"tabindex values that are not 0: {wrong}"

    scrollers = re.findall(r"<div class=\"scroll-x\"[^>]*>", markup)
    assert len(scrollers) == markup.count("<table"), "a table has no scroller"
    assert len(values) == len(scrollers), (
        f"{len(values)} tabindex attribute(s) for {len(scrollers)} scroller(s)"
    )
    for scroller in scrollers:
        assert 'tabindex="0"' in scroller, f"scroller is not focusable: {scroller}"


def test_every_focusable_scroller_carries_its_own_accessible_name() -> None:
    """Each scroller declares a role and a label, and no two labels are equal.

    Focus landing on an unnamed box announces nothing, which is a stop a
    keyboard reader cannot account for. Two boxes sharing a name is the same
    fault one step later: the second stop is indistinguishable from the first.
    """
    markup = markup_only(read_asset(INDEX))
    scrollers = re.findall(r"<div class=\"scroll-x\"[^>]*>", markup)
    assert scrollers, "no scroller found"

    labels = []
    for scroller in scrollers:
        assert 'role="region"' in scroller, f"scroller declares no role: {scroller}"
        found = re.search(r'aria-label="([^"]+)"', scroller)
        assert found is not None, f"scroller declares no accessible name: {scroller}"
        labels.append(found.group(1))
    assert len(set(labels)) == len(labels), f"two scrollers share a name: {labels}"


def test_no_rule_declares_a_sticky_offset_that_nothing_can_honour() -> None:
    """No ``position: sticky`` anywhere pairs with a ``top``.

    THE ONE THAT WAS HERE DID NOTHING, AND GREPPED AS IF IT DID. ``thead th``
    declared ``position: sticky; top: 0``, but sticky resolves against the
    nearest scroll container, which is ``.scroll-x`` and not the viewport, and
    ``.scroll-x`` is never taller than its content so it never scrolls
    vertically. Measured on the live page before the repair: a 200px page scroll
    moved the header top 276.4 -> 76.4, the full 200px. Measured after: every
    header cell moves by the whole scroll distance, and the only surviving
    sticky claim is a horizontal one.

    CONVENTIONS.md section 13.3 names decoration that reads as behaviour as its
    own failure class, which is why this bans the pairing rather than the header
    rule that happened to carry it.
    """
    offenders = tuple(
        f"{selector} -> {body}"
        for selector, body in css_rules(read_asset(STYLESHEET))
        if "position: sticky" in body and re.search(r"\btop:", body)
    )
    total = len(offenders)
    assert total == 0, f"{total} sticky rule(s) declare a top offset: {offenders}"


def test_the_first_column_is_pinned_against_a_sideways_scroll() -> None:
    """The label column is sticky at ``left: 0`` and paints its own ground.

    Scrolled fully right at 375px before this rule, the route cell sat at
    ``left: -440`` against a container at ``left: 41``, so the reader saw a
    status and a source belonging to no nameable row. Measured after: the cell
    sits at ``left: 42`` against the same container edge and the route reads.

    THE OPAQUE BACKGROUND IS PART OF THE FIX, not decoration. Cells travel
    underneath a pinned one, and a transparent pin shows them through itself.
    """
    rules = css_rules(read_asset(STYLESHEET))
    pinned = tuple(
        (selector, body)
        for selector, body in rules
        if "position: sticky" in body and "left: 0" in body
    )
    assert pinned, "no rule pins a column against a sideways scroll"

    pinned_selector = pinned[0][0]
    assert "first-child" in pinned_selector, f"the pin is not on a first column: {pinned_selector}"

    grounded = tuple(
        s for s, b in rules if "first-child" in s and re.search(r"background:\s*var\(", b)
    )
    assert grounded, "the pinned body cell declares no opaque background"


def test_the_pinned_column_is_capped_where_the_scroller_is_narrow() -> None:
    """At the narrow breakpoint the pin is bounded on BOTH sides.

    A PIN WITH NO CAP TAKES AWAY WHAT THE SCROLL WAS FOR. The route column is
    nowrap monospace sized to its longest string and measured 247px inside a
    293px container, so pinning it left 46px to scroll five columns through and
    a reader scrolled fully right saw ``ROM`` and ``alth``.

    A CAP WITH NO FLOOR IS WORSE. ``max-width`` caps a column and never asks for
    one: with ``overflow-wrap: anywhere`` the min-content width falls to a single
    character and a table whose content exceeds its box hands every shrinkable
    column exactly that. Measured at 34px wide and 589px tall, the route wrapped
    down 28 lines. Both bounds, or the rule does the opposite of its intent.
    """
    narrow = tuple(
        (selector, body)
        for selector, body in css_rules(read_asset(STYLESHEET))
        if "first-child" in selector and "max-width" in body
    )
    assert narrow, "the pinned column is never capped"

    selector, body = narrow[0]
    assert "min-width" in body, f"the cap has no floor under it: {selector} -> {body}"
    assert "white-space: normal" in body, "the cap cannot bind while the cell is nowrap"


def test_the_body_does_not_clip_a_sideways_overflow() -> None:
    """``body`` declares no ``overflow-x``, so a future overflow still shows.

    ``overflow-x: hidden`` sat here and nothing needed it: the audit walked 62
    elements past the viewport edge at 375px and found all 62 inside a working
    scroller. What it did do was swallow the signal - a scrollbar is the only
    warning a reader or an auditor gets that something has burst its container,
    and clipping removes the evidence rather than the fault.

    Re-measured after removal, with the clip gone: no page-level sideways scroll
    at 1100px or at 375px, in either colour scheme.
    """
    body = _block(read_asset(STYLESHEET), "body {")
    assert body, "no body rule found"
    assert "overflow-x" not in body, f"body clips its own overflow signal: {body.strip()}"


def test_the_live_line_outranks_the_prose_that_never_changes() -> None:
    """``.note`` is larger than ``.lede`` and takes the stronger colour token.

    ``.lede`` is prose typed into index.html, identical on every load. ``.note``
    is written by app.js out of a response body and is the line that says what
    this surface could and could not reach THIS time. The audit measured the
    ranking inverted - the live answer at 13.6px in ``--muted`` against fixed
    prose at 15px in ``--text``. Re-measured after: 15.2px in ``--text`` at
    14.38:1 against 14.4px in ``--muted`` at 6.69:1, dark scheme, both clearing
    AA and now in the right order.
    """
    rules = dict(css_rules(read_asset(STYLESHEET)))
    lede, note = rules.get(".lede", ""), rules.get(".note", "")
    assert lede, ".lede has no rule"
    assert note, ".note has no rule"

    sizes = {}
    for name, body in ((".lede", lede), (".note", note)):
        found = _FONT_SIZE.search(body)
        assert found is not None, f"{name} declares no absolute font-size"
        value = float(found.group(1))
        sizes[name] = value * ROOT_FONT_PX if found.group(2) == "rem" else value

    assert sizes[".note"] > sizes[".lede"], f"the live line is not the larger: {sizes}"
    assert "color: var(--text)" in note, f".note does not take the stronger colour: {note}"
    assert "color: var(--muted)" in lede, f".lede is not the demoted one: {lede}"


def test_both_running_prose_classes_are_capped_to_a_readable_measure() -> None:
    """``.lede`` and ``.note`` both declare a ``ch`` cap.

    ``.note`` carried no ``max-width`` at all and ran to 137 characters at
    1100px, against ``.lede`` correctly capped at 60ch - roughly twice the width
    a reader reliably tracks a line return across.
    """
    rules = dict(css_rules(read_asset(STYLESHEET)))
    for name in (".lede", ".note"):
        body = rules.get(name, "")
        assert body, f"{name} has no rule"
        found = re.search(r"max-width:\s*(\d+)ch", body)
        assert found is not None, f"{name} declares no ch measure cap: {body}"
        measure = int(found.group(1))
        assert measure <= MAX_MEASURE_CH, f"{name} is capped at {measure}ch"


def test_a_numeric_column_header_shares_the_alignment_of_its_cells() -> None:
    """Whatever right-aligns ``td.count`` right-aligns ``th.count`` too.

    ``td.count`` was right-aligned so the ones line up under the ones, while its
    header inherited the left alignment every other cell takes - which left the
    word naming the column at the opposite end of it from the numbers. The
    header carries the same class as the cells, so the pairing is one token in
    the markup rather than two rules agreeing by coincidence.
    """
    rules = css_rules(read_asset(STYLESHEET))
    aligned = tuple(selector for selector, body in rules if "text-align: right" in body)
    assert aligned, "nothing on the page is right-aligned"
    for selector in aligned:
        paired = "th.count" in selector and "td.count" in selector
        assert paired, f"a right-aligned rule does not carry its header with it: {selector}"

    markup = markup_only(read_asset(INDEX))
    assert '<th scope="col" class="count">' in markup, "no header cell claims the numeric column"


def test_no_declared_font_size_falls_below_the_floor() -> None:
    """Every absolute ``font-size`` in the sheet is at least 12px.

    THE JUDGEMENT THIS ENCODES. ``.facts dt`` at 11.52px and ``thead th`` at
    11.84px were the only strings under 12px, both uppercase and tracked at
    0.06em - the pairing that costs most at small sizes, because capitals
    flatten the profile a reader scans word shapes by and tracking pulls apart
    what is left. Both cleared AA on contrast, but contrast and legibility are
    separate measurements and neither certifies the other. Lifting them cost
    0.48px and 0.16px and nothing reflowed.

    A FLOOR IS WORTH MORE THAN THE PIXELS. Fourteen font-size declarations
    individually judged is fourteen chances to drift; one bound a test holds is
    a rule. Re-measured on the live page in both schemes: smallest rendered type
    12px, nothing below.
    """
    css = _CSS_COMMENT.sub(" ", read_asset(STYLESHEET))
    declared = _FONT_SIZE.findall(css)
    assert declared, "the sheet declares no absolute font-size at all"

    small = tuple(
        f"{value}{unit}"
        for value, unit in declared
        if (float(value) * ROOT_FONT_PX if unit == "rem" else float(value)) < MIN_FONT_PX
    )
    total = len(small)
    assert total == 0, f"{total} font-size(s) below {MIN_FONT_PX}px: {small}"


def test_the_script_no_longer_claims_avoiding_innerhtml_is_enough() -> None:
    """The header prose records that the focus fault arrived by another door.

    GRADED ON THE COMMENTS, WITH THE CODE STRIPPED. The file's header used to
    say a node-building repaint "has the same cost and not that fault", which
    the audit measured false - the rows were built as nodes exactly as described
    and a repaint still emptied the document of focus, through the button. A
    comment asserting a guarantee the code does not honour is worse than no
    comment, because the next reader stops looking.
    """
    prose = comments_only(read_asset(SCRIPT))
    assert "innerHTML" in prose, "the header no longer discusses innerHTML at all"
    assert "not on its own enough" in prose.lower(), (
        "the header does not record that avoiding innerHTML is insufficient"
    )
    assert "aria-disabled" in prose, "no comment records what replaced the disable"


# ---------------------------------------------------------------------------
# j. The page's own content: nine rows, and the blocked-by id as text
# ---------------------------------------------------------------------------


def test_the_script_names_every_published_route_template() -> None:
    """All nine of ``health.ENDPOINT_TEMPLATES`` appear in the row table.

    Read from the endpoint module rather than restated here, so a tenth route
    landing in BOOTSTRAP.md section 7.1 turns this red instead of leaving the
    page one row short and silent.
    """
    script = read_asset(SCRIPT)
    expected = len(health.ENDPOINT_TEMPLATES)
    missing = tuple(name for name in health.ENDPOINT_TEMPLATES if f'"{name}"' not in script)
    total = len(missing)
    assert total == 0, f"{total} of {expected} route templates absent from app.js: {missing}"


def test_the_script_gives_each_route_the_method_its_owner_publishes() -> None:
    """Every method the page prints is the one the endpoint module registers.

    The five unbacked routes carry their verb in ``pending.UNBACKED``; the two
    solver routes carry theirs in ``solve.METHOD_POST``. Both are read here.
    A page that printed GET beside ``/api/solve`` would be telling an operator
    to make a request the server refuses.
    """
    script = read_asset(SCRIPT)
    expected = {template: method for method, template in pending.UNBACKED} | {
        solve.SOLVE_ENDPOINT: solve.METHOD_POST,
        solve.OPTIMIZE_ENDPOINT: solve.METHOD_POST,
        health.ENDPOINT: "GET",
        WORLD_ENDPOINT: "GET",
    }
    assert len(expected) == len(health.ENDPOINT_TEMPLATES), sorted(expected)

    entries = dict(re.findall(r'template: "([^"]+)", method: "([A-Z]+)"', script))
    wrong = tuple(
        f"{template}: page says {entries.get(template)!r}, owner says {method!r}"
        for template, method in sorted(expected.items())
        if entries.get(template) != method
    )
    total = len(wrong)
    assert total == 0, f"{total} route(s) carry the wrong method: {wrong}"


#: A JavaScript block comment. Stripped before any arm that means to grade CODE.
_BLOCK_COMMENT = re.compile(r"/\*[\s\S]*?\*/")

#: One entry of ``app.js``'s ``ROUTES`` table. ``probe`` is either a quoted path
#: the page will GET or the literal ``null``, and which of the two it is decides
#: whether that row is fetched or filled from the ``/api/health`` liveness map.
_ROUTE_ENTRY = re.compile(
    r'\{\s*template:\s*"(?P<template>[^"]+)"\s*,'
    r'\s*method:\s*"(?P<method>[^"]+)"\s*,'
    r'\s*probe:\s*(?P<probe>"[^"]*"|null)\s*\}'
)


def code_only(text: str) -> str:
    """The script with its block comments removed.

    THIS EXISTS BECAUSE THE MUTATION SWEEP CAUGHT AN ARM GRADING PROSE. The
    blocked-by arm below used to search the whole file, and a comment mentioning
    ``blocked_by`` sat close enough to a ``textContent`` to satisfy it - so
    changing the property the page actually reads left the arm green. An arm
    that means "the code does this" has to be given the code.

    Args:
        text: The script's full text.

    Returns:
        The text with every block comment replaced by a space.
    """
    return _BLOCK_COMMENT.sub(" ", text)


def comments_only(text: str) -> str:
    """Just the block comments, which is what an arm about PROSE must grade.

    The complement of :func:`code_only`, and it exists for the same reason: the
    mutation sweep found an arm asserting a rationale was recorded in a comment
    that could not fail, because the same words also appear in the code.

    Args:
        text: The script's full text.

    Returns:
        Every block comment, joined by newlines.
    """
    return "\n".join(_BLOCK_COMMENT.findall(text))


def test_the_comment_splitters_are_complementary() -> None:
    """One keeps the code and drops the prose; the other does the reverse."""
    sample = "var a = 1; /* a rationale */ node.textContent = a;"
    assert "rationale" not in code_only(sample), code_only(sample)
    assert "rationale" in comments_only(sample), comments_only(sample)
    assert "textContent" not in comments_only(sample), comments_only(sample)
    assert "textContent" in code_only(sample), code_only(sample)


def test_the_comment_stripper_removes_a_comment_and_keeps_the_code() -> None:
    """The stripper is proved to do both halves of its job."""
    sample = "var a = 1; /* blocked_by lives here */ node.textContent = a;"
    stripped = code_only(sample)
    assert "blocked_by" not in stripped, stripped
    assert "node.textContent" in stripped, stripped


def test_the_script_renders_the_blocking_item_id_as_text() -> None:
    """``blocked_by`` is read off a response body and assigned to ``textContent``.

    The 501 rows are the deliverable, not a gap to disguise: five of nine routes
    have no layer beneath them and the page says which item would build them.

    GRADED ON THE CODE, WITH THE COMMENTS STRIPPED, and stated as two structural
    claims rather than as a proximity search. The proximity version passed a
    mutation that stopped reading ``blocked_by`` altogether, because a comment
    naming it sat near a ``textContent``. Both halves are asserted separately:
    the value is read off a response BODY, and the value that reaches the cell
    is the one the reader returned.
    """
    code = code_only(read_asset(SCRIPT))
    assert re.search(r"\bbody\.blocked_by\b", code), (
        "app.js does not read blocked_by off a response body"
    )
    assert re.search(r"\.textContent\s*=\s*blockedFor\(", code), (
        "the blocked-by reader's value is not assigned to a textContent"
    )
    assert "blockedFor" in code, "the reader named by the assignment does not exist"


def test_the_script_never_hardcodes_the_blocking_item_id() -> None:
    """``CS-500`` is read off the wire, never typed into the page.

    A hardcoded id renders the same characters whether or not the server agrees,
    which is a page that cannot go wrong and therefore cannot be right either.
    """
    script = read_asset(SCRIPT)
    markup = read_asset(INDEX)
    assert pending.PENDING_BLOCKER not in script, "app.js hardcodes the blocking item id"
    assert pending.PENDING_BLOCKER not in markup, "index.html hardcodes the blocking item id"


def test_the_page_shows_the_two_version_facts_and_the_two_presence_badges() -> None:
    """The header line and the badges read the health body's own keys."""
    script = read_asset(SCRIPT)
    absent = tuple(key for key in health.DATA_KEYS if f'"{key}"' not in script)
    total = len(absent)
    assert total == 0, f"{total} health key(s) the page never reads: {absent}"


def test_the_page_shows_the_masked_token_and_the_world_scalars() -> None:
    """Every top-level ``/api/world`` key is read, including the counts."""
    script = read_asset(SCRIPT)
    absent = tuple(
        key for key in ("world", "counts", "unknown_classes") if f'"{key}"' not in script
    )
    total = len(absent)
    assert total == 0, f"{total} world key(s) the page never reads: {absent}"

    scalars = ("header_version", "save_version", "build_changelist", "body_offset")
    unread = tuple(key for key in scalars if f'"{key}"' not in script)
    assert not unread, f"version scalars the page never reads: {unread}"


def test_the_page_issues_no_post_and_no_form() -> None:
    """GET only, and no form to submit. CSRF is absent by construction.

    The walking skeleton reads solve and optimize liveness from the health
    body's endpoint map instead of exercising either route, so there is nothing
    on this page that changes server state and nothing to forge a request to.
    """
    code = code_only(read_asset(SCRIPT))
    markup = read_asset(INDEX)
    assert "<form" not in markup, "the page carries a form"

    table = re.search(r"var ROUTES = \[[\s\S]*?\n\];", code)
    assert table is not None, "the route table is not where this arm expects it"

    outside = code.replace(table.group(0), " ")
    assert "POST" not in outside, "app.js names POST outside its own route table"

    verbs = re.findall(r"method: \"([A-Z]+)\"", table.group(0))
    posts = tuple(verb for verb in verbs if verb == "POST")
    expected_posts = 3
    assert len(posts) == expected_posts, f"the route table names {len(posts)} POST verb(s)"

    calls = re.findall(r"fetch\([\s\S]{0,200}?method: \"([A-Z]+)\"", code)
    assert calls, "no fetch call names a method at all"
    assert set(calls) == {"GET"}, f"a fetch issues something other than GET: {sorted(set(calls))}"


# ---------------------------------------------------------------------------
# k. Nothing in this slice claims a port from the reserved band
# ---------------------------------------------------------------------------


def test_no_file_in_this_slice_names_a_reserved_dashboard_port() -> None:
    """The band belongs to ``config/ports.json``; this slice binds port zero."""
    here = Path(__file__).resolve()
    files = [WEB_DIR / name for name in ASSET_NAMES] + [here, here.parent / "audit_harness.py"]
    findings: list[str] = []
    for path in files:
        if not path.is_file():
            continue
        text = path.read_bytes().decode("ascii")
        findings.extend(
            f"{path.name}: {value}"
            for value in re.findall(r"\b(\d{4})\b", text)
            if PORT_BAND_FIRST <= int(value) <= PORT_BAND_LAST
        )
    total = len(findings)
    assert total == 0, f"{total} reserved-band port literal(s) in this slice: {findings}"


# ===========================================================================
# l. tests/surface/audit_harness.py - the plain-HTTP stand-in the audit needs
# ===========================================================================
#
# WHY A SECOND SERVER EXISTS AT ALL. Measured in this session: the browser pane
# refuses to load HTTPS backed by a self-signed certificate - it is denied
# BEFORE the TLS handshake, so no screenshot of the real dashboard is possible.
# Plain HTTP on loopback renders and screenshots fine. BOOTSTRAP.md section 7.1
# mandates HTTPS for the dashboard, so the production server cannot move to
# HTTP; the stand-in is what lets the CS-600 five-phase visual audit grade the
# REAL page, served from the REAL asset files, in a REAL populated state.
#
# THE ARMS BELOW GRADE THE STAND-IN ITSELF, because a harness that served a
# fabricated page would make the audit a verdict about nothing.


def get(port: int, path: str) -> tuple[int, bytes, str]:
    """Issue one GET against the harness and return code, body and content type.

    ``http.client`` rather than ``urllib.request``: the latter takes its scheme
    from its argument, which is the thing bandit's S310 is written about, and
    this needs neither the generality nor the suppression.

    Args:
        port: The harness's bound port.
        path: The request path.

    Returns:
        The status code, the body bytes and the ``Content-Type`` header.
    """
    connection = http.client.HTTPConnection(config.LOOPBACK, port, timeout=SOCKET_TIMEOUT)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        return response.status, response.read(), response.headers.get("Content-Type", "")
    finally:
        connection.close()


@pytest.fixture(scope="module")
def harness() -> Iterator[audit_harness.AuditHarness]:
    """Start the stand-in once for this module and stop it however the run ends."""
    running = audit_harness.AuditHarness()
    running.start()
    try:
        yield running
    finally:
        running.stop()


def test_the_harness_binds_an_ephemeral_port_outside_the_reserved_band(
    harness: audit_harness.AuditHarness,
) -> None:
    """It asks the operating system for a port rather than claiming one.

    ``config/ports.json`` owns the dashboard's allocation. A test server that
    claimed a number from that band would collide with the real listener the
    moment both ran, and the collision would surface as an unexplained bind
    failure in whichever started second.
    """
    assert audit_harness.REQUESTED_PORT == 0, "the harness does not request an ephemeral port"
    bound = harness.port
    assert bound > 0, "the harness reports no bound port"
    assert not PORT_BAND_FIRST <= bound <= PORT_BAND_LAST, f"bound in the reserved band: {bound}"


def test_the_harness_serves_the_three_real_asset_files(
    harness: audit_harness.AuditHarness,
) -> None:
    """Every static route returns the bytes on disk, byte for byte.

    THIS IS THE ARM THAT MAKES THE AUDIT MEAN ANYTHING. An audit run against a
    page the harness invented would grade a document this project does not ship.
    Comparing raw bytes - not a substring, not a length - is what forecloses it.
    """
    mismatched: list[str] = []
    for path, (name, content_type) in sorted(server.STATIC_ROUTES.items()):
        code, body, served_type = get(harness.port, path)
        on_disk = (WEB_DIR / name).read_bytes()
        if code != HTTP_OK or body != on_disk:
            mismatched.append(f"{path}: code={code}, {len(body)} bytes of {len(on_disk)}")
        elif not served_type.startswith(content_type.split(";")[0]):
            mismatched.append(f"{path}: served as {served_type!r}, table says {content_type!r}")
    total = len(mismatched)
    assert total == 0, f"{total} static route(s) did not serve the real file: {mismatched}"


def test_the_harness_refuses_a_path_it_does_not_publish(
    harness: audit_harness.AuditHarness,
) -> None:
    """Anything outside the published tables is a contract 404, not a stack trace."""
    code, body, _type = get(harness.port, "/nothing/here")
    assert code == HTTP_NOT_FOUND, code
    payload = json.loads(body)
    assert payload["reason"] == contract.REASON_NO_SUCH_ROUTE, payload
    assert payload["endpoint"] == contract.ENDPOINT_UNROUTED, payload


def test_the_harness_serves_no_stand_in_path_for_either_id_template(
    harness: audit_harness.AuditHarness,
) -> None:
    """Neither ``<id>`` template gets a concrete path here, so both 404.

    WHAT THIS DOES AND DOES NOT CLAIM. It verifies ONE thing: the harness's
    exact-path table carries no invented id, so a request for one is the
    contract's 404. It does NOT claim production cannot route these - production
    routes both and answers 501, which is the opposite of what the justification
    on this arm used to say. The reason the stand-in still serves neither is that
    the audited page asks for neither, and that premise is pinned separately by
    :func:`test_the_page_asks_for_no_concrete_path_on_either_id_template` rather
    than restated here. ``tests/surface/audit_harness.py`` carries the whole
    reasoning.
    """
    parameterised = tuple(name for name in health.ENDPOINT_TEMPLATES if "<" in name)
    found = len(parameterised)
    expected = 2
    assert found == expected, f"expected {expected} path-parameter templates, found {found}"

    answered = tuple(
        name
        for name in parameterised
        if get(harness.port, name.replace("<id>", "probe"))[0] != HTTP_NOT_FOUND
    )
    served = len(answered)
    assert served == 0, f"the harness serves a stand-in id for: {answered}"


def probe_paths(text: str) -> dict[str, str | None]:
    """Each route the page publishes, mapped to the path it will GET, or None.

    Reads ``app.js``'s own ``ROUTES`` table out of the shipped bytes. A route
    whose ``probe`` is ``null`` is one the page never requests, so its row is
    filled from the ``/api/health`` liveness map instead.

    Args:
        text: The script's text, comments already stripped by :func:`code_only`.

    Returns:
        Template to probe path, or to None where the entry declares ``null``.
    """
    return {
        match.group("template"): (
            None if match.group("probe") == "null" else match.group("probe").strip("\"'")
        )
        for match in _ROUTE_ENTRY.finditer(text)
    }


def test_the_page_asks_for_no_concrete_path_on_either_id_template() -> None:
    """The premise the harness's three-not-five decision rests on, pinned.

    THIS IS THE ARM THAT MAKES THAT DECISION FALSIFIABLE. The harness serves no
    stand-in id because the page requests neither ``<id>`` route - so both rows
    read from ``/api/health`` and adding canned answers would change no rendered
    byte. That is a fact about ``app.js``, and a fact stated only in a docstring
    is one that goes stale silently; the justification on the sibling arm above
    already did exactly that once. The day either row gains a probe path, this
    goes red and the harness has to be revisited.
    """
    routes = probe_paths(code_only(read_asset(SCRIPT)))
    published = len(routes)
    expected = len(health.ENDPOINT_TEMPLATES)
    assert published == expected, f"parsed {published} route entries, expected {expected}"

    asked = tuple(
        template for template, probe in routes.items() if "<" in template and probe is not None
    )
    count = len(asked)
    assert count == 0, f"the page now asks for a concrete path on: {asked}"


def test_the_probe_path_detector_sees_a_planted_concrete_id() -> None:
    """The detector is proved able to fire, on the exact edit it exists to catch.

    A parser that silently matched nothing would make the arm above green over a
    page that probes every route. Planting one concrete id must be seen.
    """
    clean = code_only(read_asset(SCRIPT))
    parsed = probe_paths(clean)
    assert parsed, "the route table parsed to nothing; the detector grades nothing"

    target = next(template for template in parsed if "<" in template)
    planted = clean.replace(
        f'{{ template: "{target}", method: "GET", probe: null }}',
        f'{{ template: "{target}", method: "GET", probe: "/api/advice/planted/derivation" }}',
    ).replace(
        f'{{ template: "{target}", method: "POST", probe: null }}',
        f'{{ template: "{target}", method: "POST", probe: "/api/advice/planted/state" }}',
    )
    assert planted != clean, f"the mutation never applied to {target}"

    after = probe_paths(planted)
    seen = after.get(target)
    assert seen is not None, f"the detector read {target} as unprobed after planting a path"


def test_the_harness_publishes_five_not_implemented_bodies_naming_the_open_item(
    harness: audit_harness.AuditHarness,
) -> None:
    """One 501 per unbacked route, each built by the shipped constructor.

    The bodies are built by ``contract.not_implemented``, so they cannot drift
    from what the real endpoints produce and cannot name an item the contract
    does not still hold open.
    """
    expected = len(pending.UNBACKED)
    published = audit_harness.PENDING_BODIES
    assert len(published) == expected, sorted(published)

    wrong = tuple(
        f"{template}: {response.http_status} {response.payload.get('blocked_by')!r}"
        for template, response in sorted(published.items())
        if response.http_status != contract.HTTP_NOT_IMPLEMENTED
        or response.payload.get("blocked_by") != pending.PENDING_BLOCKER
    )
    total = len(wrong)
    assert total == 0, f"{total} pending body(ies) are not a 501 naming the open item: {wrong}"

    served = tuple(
        template
        for template in sorted(published)
        if "<" not in template and get(harness.port, template)[0] != contract.HTTP_NOT_IMPLEMENTED
    )
    assert not served, f"routable pending endpoints that did not answer 501: {served}"


def test_every_canned_body_satisfies_the_shipped_contract_checker(
    harness: audit_harness.AuditHarness,
) -> None:
    """``contract.contract_problems`` finds nothing wrong with any canned answer.

    Reusing the project's own checker is what keeps the harness honest without a
    second description of the envelope living in this file.
    """
    assert harness.port > 0
    findings = {
        key: contract.contract_problems(response)
        for key, response in audit_harness.CANNED.items()
        if contract.contract_problems(response)
    }
    total = len(findings)
    assert total == 0, f"{total} canned response(s) violate the contract: {findings}"


def test_every_canned_body_encodes_as_seven_bit_ascii_with_no_float(
    harness: audit_harness.AuditHarness,
) -> None:
    """Each canned payload survives ``contract.encode``, which refuses both."""
    assert harness.port > 0
    encoded = {
        key: contract.encode(response.payload) for key, response in audit_harness.CANNED.items()
    }
    assert encoded, "the harness publishes no canned bodies at all"

    high = tuple(key for key, raw in sorted(encoded.items()) if offending_bytes(raw))
    assert not high, f"canned bodies with bytes above 0x7E: {high}"


def test_the_harness_health_body_carries_the_shape_the_endpoint_publishes(
    harness: audit_harness.AuditHarness,
) -> None:
    """Same top-level keys, same data keys, same nine-entry liveness map."""
    code, body, _type = get(harness.port, health.ENDPOINT)
    assert code == HTTP_OK, code
    payload = json.loads(body)
    assert set(payload) == set(contract.PAYLOAD_KEYS_OK), sorted(payload)

    data = payload["data"]
    assert set(data) == set(health.DATA_KEYS), sorted(data)
    assert data["registry"] in health.PRESENCE_WORDS, data["registry"]
    assert data["world"] in (health.LOADED, health.ABSENT), data["world"]

    endpoints = data["endpoints"]
    assert tuple(sorted(endpoints)) == tuple(sorted(health.ENDPOINT_TEMPLATES)), sorted(endpoints)
    outside = tuple(
        name for name, word in sorted(endpoints.items()) if word not in health.LIVENESS_WORDS
    )
    assert not outside, f"liveness words outside the published vocabulary: {outside}"

    unbacked = {template for _method, template in pending.UNBACKED}
    disagreeing = tuple(name for name in sorted(unbacked) if endpoints.get(name) != health.NOT_LIVE)
    assert not disagreeing, f"unbacked routes the harness calls live: {disagreeing}"


def test_the_harness_world_body_carries_the_shape_the_endpoint_publishes(
    harness: audit_harness.AuditHarness,
) -> None:
    """Same data keys, same count keys, same unlock keys, and a masked token."""
    code, body, _type = get(harness.port, WORLD_ENDPOINT)
    assert code == HTTP_OK, code
    data = json.loads(body)["data"]
    assert set(data) == set(world.DATA_KEYS), sorted(data)
    assert set(data["counts"]) == set(world.COUNT_KEYS), sorted(data["counts"])
    assert set(data["unlocks"]) == set(world.UNLOCK_KEYS), sorted(data["unlocks"])

    assert data["unknown_classes"], "no unmodeled classes, so the page's list renders empty"
    misshaped = tuple(
        str(sorted(entry))
        for entry in data["unknown_classes"]
        if set(entry) != set(world.UNKNOWN_CLASS_KEYS)
    )
    assert not misshaped, f"unknown_classes entries off shape: {misshaped}"

    off = tuple(
        str(sorted(entry)) for entry in data["warnings"] if set(entry) != set(world.WARNING_KEYS)
    )
    assert not off, f"warning entries off shape: {off}"


def test_the_harness_world_token_is_a_digest_of_an_openly_synthetic_seed(
    harness: audit_harness.AuditHarness,
) -> None:
    """The masked token is the shipped mask over a seed authored in this repo.

    Deriving it through ``clockspeed.save.header.masked_token`` rather than
    typing a hex string is what makes the SHAPE identical to production while
    the INPUT is a sentence this repository wrote. A real token never comes near
    this file.
    """
    code, body, _type = get(harness.port, WORLD_ENDPOINT)
    assert code == HTTP_OK, code
    served = json.loads(body)["data"]["world"]
    assert served == masked_token(audit_harness.SYNTHETIC_WORLD_SEED), served
    assert served.startswith(MASK_PREFIX), served
    assert len(served) == len(MASK_PREFIX) + MASK_DIGEST_CHARACTERS, served
    assert "synthetic" in audit_harness.SYNTHETIC_WORLD_SEED, "the seed does not declare itself"


def personal_data_findings(blob: str) -> tuple[str, ...]:
    """Every personal-data shape present in one blob of served text.

    Searched BY SHAPE rather than by value, because the harness has to stay safe
    on a machine whose account name, world name and save path this test cannot
    know. The four classes are the ones CLAUDE.md section 2 and non-negotiable 3
    name: the Windows account, a home path, a platform account id, a world.

    Args:
        blob: The decoded text to sweep.

    Returns:
        One finding per shape present, sorted by label.
    """
    shapes = {
        "drive-lettered path": re.compile(r"[A-Za-z]:[\\/]"),
        "platform-account-shaped digits": re.compile(r"\d{12,}"),
        "hex account id": re.compile(r"\b[0-9a-fA-F]{32,}\b"),
        "user profile path": re.compile(r"[Uu]sers[\\/]"),
        "save file extension": re.compile(r"\.sav\b"),
        "save directory marker": re.compile(r"SaveGames|LOCALAPPDATA"),
    }
    findings: list[str] = []
    for label, pattern in sorted(shapes.items()):
        found = pattern.search(blob)
        if found is not None:
            findings.append(f"{label}: {found.group(0)!r}")
    return tuple(findings)


def test_no_canned_body_carries_anything_that_could_be_personal_data(
    harness: audit_harness.AuditHarness,
) -> None:
    """Every canned byte is swept for the classes CLAUDE.md names."""
    assert harness.port > 0
    blob = b"\n".join(
        contract.encode(response.payload) for response in audit_harness.CANNED.values()
    ).decode("ascii")
    assert blob, "there is nothing to sweep"

    literals = {
        "account name": getpass.getuser(),
        "home directory": str(Path.home()),
    }
    named = tuple(label for label, needle in sorted(literals.items()) if needle and needle in blob)
    assert not named, f"canned bodies carry: {named}"

    matched = personal_data_findings(blob)
    total = len(matched)
    assert total == 0, f"{total} personal-data shape(s) in the canned bodies: {matched}"


def test_the_personal_data_sweep_fires_on_every_shape_it_claims() -> None:
    """The sweep is proved to catch each shape it names.

    Without this, a sweep that found nothing and a sweep that could find nothing
    are the same green - the exact failure a sibling slice hit this session,
    where a traversal arm passed because its target file did not exist.
    """
    assert personal_data_findings("nothing to see here") == ()

    planted = (
        "C:/some/path",
        "id 765611980000000",
        "acct 0123456789abcdef0123456789abcdef",
        "under Users/somebody",
        "world.sav ",
        "under SaveGames",
    )
    silent = tuple(sample for sample in planted if not personal_data_findings(sample))
    assert not silent, f"the personal-data sweep did not fire on: {silent}"


def test_the_harness_is_test_code_and_no_shipping_module_reaches_it() -> None:
    """It lives under ``tests/`` and nothing under ``clockspeed/`` names it.

    A stand-in that answers on plain HTTP and was reachable from the shipping
    package would be a way to serve this dashboard without TLS, which
    BOOTSTRAP.md section 7.1 forbids.
    """
    module_path = Path(audit_harness.__file__).resolve()
    assert module_path.parent.name == "surface", module_path
    assert module_path.parent.parent.name == "tests", module_path

    package = Path(server.__file__).resolve().parent.parent
    sources = sorted(package.rglob("*.py"))
    assert sources, "the shipping package sweep found no modules; it would be vacuous"

    importers = tuple(
        source.relative_to(package.parent).as_posix()
        for source in sources
        if "audit_harness" in source.read_bytes().decode("ascii")
    )
    total = len(importers)
    assert total == 0, f"{total} shipping module(s) name the harness: {importers}"


def test_no_file_in_this_slice_holds_a_carriage_return() -> None:
    """All five slice files are LF-terminated, asserted on raw bytes.

    ``write_text`` converts LF to CRLF on Windows and ``read_text`` hides it, so
    a byte count is the only reading that sees the fault. Git normalises the
    blob and reports the tree clean while the working tree violates the rule.
    """
    here = Path(__file__).resolve()
    files = [WEB_DIR / name for name in ASSET_NAMES] + [here, here.parent / "audit_harness.py"]
    expected = 5
    assert len(files) == expected, files

    findings = {
        path.name: path.read_bytes().count(b"\r")
        for path in files
        if path.read_bytes().count(b"\r") > 0
    }
    total = len(findings)
    assert total == 0, f"carriage returns in {total} slice file(s): {findings}"
