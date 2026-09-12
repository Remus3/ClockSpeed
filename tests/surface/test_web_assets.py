"""CS-601 slice S5 - the dashboard's static assets, graded at rest.

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
import socket
from pathlib import Path
from typing import TYPE_CHECKING, Final, NamedTuple

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

#: The panel modules, in the order ``index.html`` loads them. CS-962 split the
#: page's panels out of ``app.js`` so a future panel is a NEW FILE rather than
#: an edit to the one script every other panel also wants to edit. The seam
#: itself - ``registerPanel`` and the mount loop - stays in ``app.js``, which is
#: why that file is still named apart from these four.
PANEL_MODULES: Final = (
    "panel_registry.js",
    "panel_scope.js",
    "panel_solve.js",
    "panel_warnings.js",
    "panel_map.js",
)

#: The route template ``clockspeed/surface/api/world.py`` answers. Spelled here
#: rather than imported because that module names it ``ENDPOINT``, which would
#: collide with ``health.ENDPOINT`` at any shared import site.
WORLD_ENDPOINT: Final = "/api/world"

#: The route template ``clockspeed/surface/api/registry.py`` answers, spelled
#: here for the same reason and no other: that module also names it
#: ``ENDPOINT``. CS-912 added it under BOOTSTRAP.md section 7.1's word "minimum".
REGISTRY_ENDPOINT: Final = "/api/registry"

#: The route template ``clockspeed/surface/api/map.py`` answers, spelled here for
#: the third time for the same reason: that module also names it ``ENDPOINT``.
#: CS-977 added it the way CS-912 added its predecessor.
MAP_ENDPOINT: Final = "/api/map"

#: The highest byte the project's character-set rule admits. Restated from
#: nowhere: it is the same 0x7E ``contract.MAX_ASCII_BYTE`` and the commit gate
#: both use, and it is spelled here because a test that imports a constant to
#: assert the constant grades nothing.
MAX_ASCII_BYTE: Final = 0x7E

#: How long a request against the loopback stand-in may take before it is a
#: failure rather than a slow machine.
SOCKET_TIMEOUT: Final = 10.0

HTTP_OK: Final = 200

#: Seconds to wait when probing whether a stopped harness released its port.
SOCKET_PROBE_SECONDS: Final = 0.5
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


def test_the_server_names_exactly_the_assets_the_page_loads() -> None:
    """The name set this module grades is the server's own, and it is the page's.

    An arm that grades a name set it invented would stay green while the server
    served one more file nobody checked. THE COUNT IS NOT WRITTEN DOWN: it is
    the page, the sheet, the script and the panel modules ``index.html`` loads,
    derived from :data:`PANEL_MODULES` rather than restated beside it, because a
    number typed next to a list it does not come from has no way of staying
    right - CLAUDE.md section 4.

    A PANEL MODULE THE SERVER DOES NOT NAME IS A FILE THE PAGE CANNOT LOAD, and
    since ``STATIC_ROUTES`` is a literal by design - no directory walk - the
    name has to be added there on purpose. This arm is what makes forgetting it
    a red suite rather than a blank panel.
    """
    expected = 3 + len(PANEL_MODULES)
    assert len(ASSET_NAMES) == expected, ASSET_NAMES
    assert set(ASSET_NAMES) == {INDEX, STYLESHEET, SCRIPT, *PANEL_MODULES}, ASSET_NAMES


def test_every_named_asset_exists_on_disk() -> None:
    """Each file the static table names is present and non-empty.

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
# b. Character set - 7-bit ASCII in every byte of every asset
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

#: The SVG namespace URI, and the ONE exemption this leg carries.
#:
#: IT IS A NAME AND NEVER A REQUEST. ``document.createElementNS`` takes it to
#: decide which element interface to construct; no user agent dereferences it,
#: and there is no other way to build an SVG element that paints - an element
#: made with ``createElement("svg")`` is an unknown HTML element. So CS-977's map
#: panel cannot exist without this string, and banning it would ban the feature
#: rather than the leak.
#:
#: THE EXEMPTION IS A CONTEXT AND NOT A SPELLING, which is the difference between
#: an allowlist and a hole. What is admitted is this URI sitting INSIDE a
#: ``createElementNS`` call; the same characters in an ``href``, a ``src`` or a
#: CSS ``url()`` are a finding, and
#: :func:`test_the_svg_namespace_is_admitted_only_inside_a_createelementns_call`
#: proves both halves.
SVG_NAMESPACE: Final = "http://www.w3.org/2000/svg"

#: The one legal position: ``document.createElementNS("<the URI>"`` - up to and
#: including the comma, so a bare mention outside a call matches nothing.
_NAMESPACE_CALL: Final = re.compile(
    r"""document\.createElementNS\(\s*["']""" + re.escape(SVG_NAMESPACE) + r"""["']\s*,"""
)


def _exempt_spans(text: str) -> tuple[tuple[int, int], ...]:
    """The character ranges a remote-reference finding is admitted inside.

    Args:
        text: The asset's text.

    Returns:
        One ``(start, end)`` span per legal ``createElementNS`` call.
    """
    return tuple(match.span() for match in _NAMESPACE_CALL.finditer(text))


def remote_references(text: str) -> tuple[str, ...]:
    """Every remote-resource reference in one asset's text.

    THREE SHAPES, EACH A REAL WAY A THIRD PARTY GETS THE OPERATOR'S IP AND
    REFERER: an absolute ``http``/``https`` URL, a protocol-relative ``//host``
    reference, and a stylesheet ``@import``. "Local. Nothing is uploaded." is a
    property of the shipped bytes, not only of the response header.

    ONE EXEMPTION, BY CONTEXT: :data:`SVG_NAMESPACE` inside a
    ``createElementNS`` call. See that constant for why a namespace URI is not a
    fetch and why the admission is a position rather than a spelling.

    Args:
        text: The asset's text.

    Returns:
        One finding per match, in file order.
    """
    exempt = _exempt_spans(text)
    findings: list[str] = []
    for label, pattern in (
        ("absolute-url", _ABSOLUTE_URL),
        ("protocol-relative", _PROTOCOL_RELATIVE),
        ("css-import", _ANY_IMPORT),
    ):
        findings.extend(
            f"{label}: {match.group(0)!r}"
            for match in pattern.finditer(text)
            if not any(start <= match.start() and match.end() <= end for start, end in exempt)
        )
    return tuple(findings)


def test_no_asset_references_a_remote_resource() -> None:
    """No asset names anything off this machine."""
    findings = {
        name: remote_references(read_asset(name))
        for name in ASSET_NAMES
        if remote_references(read_asset(name))
    }
    total = len(findings)
    assert total == 0, f"remote references in {total} asset(s): {findings}"


def test_the_svg_namespace_is_admitted_only_inside_a_createelementns_call() -> None:
    """The one exemption is a position, and every other position still fires.

    BOTH HALVES, because an exemption that is only proved to admit is a hole
    nobody has measured. The shipped assets are asserted clean WITH the URI
    present in at least one of them - so the exemption is doing work - and the
    same characters planted in an ``href``, a ``src`` and a CSS ``url()`` are
    each asserted to be found.
    """
    carriers = tuple(name for name in ASSET_NAMES if SVG_NAMESPACE in read_asset(name))
    assert carriers, (
        "no shipped asset names the SVG namespace, so this exemption admits "
        "nothing and the arm below grades a rule with no subject"
    )
    for name in carriers:
        text = read_asset(name)
        assert remote_references(text) == (), f"{name} is not clean under the exemption"
        assert _exempt_spans(text), f"{name} names the namespace outside a createElementNS call"

    clean = read_asset(STYLESHEET)
    assert remote_references(clean) == ()
    planted = {
        "href": clean + "\n.f::before { content: \"<a href='" + SVG_NAMESPACE + "'>\"; }\n",
        "src": clean + "\n.f { --x: \"<img src='" + SVG_NAMESPACE + "'>\"; }\n",
        "url": clean + '\n.f { background: url("' + SVG_NAMESPACE + '"); }\n',
        "bare": clean + "\n.f { --x: " + SVG_NAMESPACE + "; }\n",
    }
    silent = tuple(shape for shape, text in planted.items() if not remote_references(text))
    assert not silent, f"the namespace exemption admitted a real reference in: {silent}"


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


def test_the_page_links_only_its_own_local_assets() -> None:
    """``index.html`` pulls in the sheet, the script and the panels, and no more.

    Counting the tags is what makes this a claim about the WHOLE document
    rather than about the two tags that happen to be correct.

    THE SCRIPT ORDER IS PART OF THE ASSERTION, not incidental to it. ``app.js``
    defines ``registerPanel`` and every panel module calls it at load, so a page
    that loaded a panel first would throw on a name that does not exist yet.
    Both are ``defer``, which runs them in document order, so the order written
    here is the order they execute in.

    CS-875 SWEEP: comments come out first. This is an equality over every href
    and src in the file, so an ``href`` inside an HTML comment could stand in
    for a real link that had been deleted and the tuple would still compare
    equal.
    """
    markup = markup_only(read_asset(INDEX))
    hrefs = tuple(re.findall(r'href="([^"]*)"', markup))
    sources = tuple(re.findall(r'src="([^"]*)"', markup))
    assert hrefs == (STYLESHEET,), hrefs
    assert sources == (SCRIPT, *PANEL_MODULES), sources


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
    """No asset schedules work, and the page registers a click handler.

    THE TWO HALVES READ DIFFERENT TEXT ON PURPOSE. The timer half is a BAN, and
    a ban over raw text can only ever fail early - a timer named in a comment
    is a false red, never a false green - so it keeps the whole file. The click
    handler is a PRESENCE claim, and CS-875 measured what that costs on raw
    text: a comment naming the handler satisfied it while nothing registered
    one. That half reads code, and matches a call.
    """
    findings = {name: timers(read_asset(name)) for name in ASSET_NAMES if timers(read_asset(name))}
    total = len(findings)
    assert total == 0, f"timer primitives in {total} asset(s): {findings}"

    code = code_only(read_asset(SCRIPT))
    handler = re.search(r'\.addEventListener\(\s*"click"', code)
    assert handler is not None, "app.js registers no click handler"


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
    #
    # SCOPED TO THE INNER :root, NOT TO THE WHOLE MEDIA BLOCK. Reading the whole
    # query counted a token declared anywhere inside it, including PAST the
    # :root closer where the browser applies nothing - so the light side was
    # measured against a rule body and the dark side against a container, and a
    # token paired only in the container's eyes passed. Measured: a planted pair
    # whose dark half sat inside the media block but outside :root reported
    # 34/34 with zero unpaired while the browser never applied the dark value.
    # The guard could not see the fault it is named for.
    #
    dark_root = _block(dark_query, ":root {")
    assert dark_root, "no :root inside the prefers-color-scheme: dark query"
    dark = set(_VAR_DECLARE.findall(dark_root))

    unpaired = tuple(sorted(light ^ dark))
    total = len(unpaired)
    assert total == 0, f"{total} token(s) defined in only one scheme: {unpaired}"


def test_the_harness_answers_every_route_it_publishes_as_live() -> None:
    """A route the harness calls live must have an answer behind it.

    ``audit_harness._liveness`` derives its map by subtracting
    ``pending.UNBACKED`` from ``health.ENDPOINT_TEMPLATES``, so a route that
    gains a layer flips to live for free - which is the behaviour that function
    advertises and wants. ``_canned`` gains nothing automatically, and the two
    halves drifted the moment CS-912 published the tenth route: the harness
    reported ``/api/registry`` live and then answered it 404, so the mandatory
    CONVENTIONS 13.2 ritual graded the page in a state production never reaches
    and showed a red pill that was an artifact of the instrument.

    THE WHOLE SUITE STAYED GREEN THROUGH THAT, which is the point of this arm.
    A template carrying a path parameter is exempt for the reason the harness
    module docstring gives - the table is keyed by exact path and the page asks
    for neither - and that exemption is derived from the template rather than
    listed, so it cannot quietly cover a parameterless route.
    """
    answered = {path for _method, path in audit_harness.CANNED}
    live = {
        template
        for template, word in audit_harness.LIVENESS.items()
        if word == health.LIVE and "<" not in template
    }
    assert live, "the harness reports no parameterless route as live; this arm is vacuous"

    unanswered = tuple(sorted(live - answered))
    total = len(unanswered)
    assert total == 0, (
        f"{total} route(s) the harness calls live have no canned answer, so the "
        f"audit grades a 404 production never returns: {unanswered}"
    )


#: The only three rules allowed to carry colour. Everything else reads a token,
#: so that redefining the tokens on ``.hud-overlay`` really does repaint the
#: whole subtree. The dark ``:root`` appears under the same selector as the
#: light one, which is why this is a set of two names and not of three.
_COLOUR_BLOCKS: Final = frozenset({":root", ".hud-overlay"})

#: Properties that can put a colour on the screen. A declaration of one of
#: these outside the three blocks must read a token, whatever notation it would
#: otherwise use.
_COLOUR_BEARING: Final = frozenset(
    {
        "color",
        "background",
        "background-color",
        "background-image",
        "border",
        "border-color",
        "border-top",
        "border-right",
        "border-bottom",
        "border-left",
        "border-top-color",
        "border-right-color",
        "border-bottom-color",
        "border-left-color",
        "outline",
        "outline-color",
        "box-shadow",
        "text-shadow",
        "text-decoration-color",
        "column-rule-color",
        "caret-color",
        "accent-color",
        "fill",
        "stroke",
        # scrollbar-color IS THE USER-AGENT-PAINTED SURFACE ROUNDS 5 AND 6 WERE
        # ABOUT, one step further out again: it colours the same scrollbar
        # `color-scheme` selects a palette for, and it takes a literal.
        "scrollbar-color",
        # -webkit-text-fill-color OVERRIDES `color` outright where supported,
        # so a check that watched only `color` would miss the paint entirely.
        "-webkit-text-fill-color",
        # The shorthands whose longhands were already listed. A shorthand is
        # the obvious way past a longhand-only list.
        "text-decoration",
        "column-rule",
        "text-emphasis",
        "text-emphasis-color",
        "border-image",
        "border-block-color",
        "border-inline-color",
    }
)

#: The values of a colour-bearing property that name no colour, and so need no
#: token behind them.
_COLOURLESS_VALUES: Final = frozenset(
    {"none", "inherit", "initial", "unset", "revert", "transparent", "currentcolor", "auto", "0"}
)

#: One `property: value` pair out of a whitespace-normalised rule body.
#:
#: THE TRAILING SEMICOLON IS OPTIONAL AND REQUIRING IT DEFEATED THE WHOLE LEG.
#: CSS lets the last declaration in a block omit it, so `color: black` with no
#: semicolon was invisible to every check built on this pattern - one character,
#: every property at once. Measured: the same literal is caught with the
#: semicolon and missed without it, and Chromium paints them identically.
_DECLARATIONS: Final = re.compile(r"([a-zA-Z-]+)\s*:\s*([^;]+?)\s*(?:;|$)")

#: A custom property declaration together with its value. Case-insensitive on
#: the NAME because custom property names are case-sensitive in CSS: an earlier
#: version declared with ``[A-Za-z0-9-]`` and compared with ``[a-z0-9-]``, so an
#: uppercase token drifted silently past the value check.
_VAR_DECLARED_VALUE: Final = re.compile(r"(--[A-Za-z0-9-]+):\s*([^;]+);")


def _token_sourced(value: str) -> bool:
    """Whether a colour-bearing value takes its colour from something redefinable.

    THERE ARE EXACTLY TWO SANCTIONED SOURCES. A custom property, which
    ``.hud-overlay`` redefines; or ``currentColor``, which IS the element's own
    ``color`` - and ``color`` is a colour-bearing property this same leg checks,
    so a value resting on it is token-sourced one step removed rather than
    exempt. ``.hud-status`` uses the second: ``border: 1px solid currentColor``
    tracks whichever ``--status-*`` the chip is carrying.

    Args:
        value: The declaration's value, whitespace-normalised.

    Returns:
        Whether the value names no colour, or names one that a token supplies.
    """
    #
    # EVERY COMMA-SEPARATED PART IS CHECKED, NOT THE VALUE AS A WHOLE. A
    # substring test for `var(--` passed a literal riding ALONGSIDE a token -
    # `box-shadow: 0 0 0 2px #ff0000, 0 0 0 4px var(--border)` was green, and
    # this sheet already uses that multi-part shape. Each part must stand up on
    # its own.
    #
    for part in value.split(","):
        lowered = part.strip().lower()
        if not lowered:
            continue
        if lowered in _COLOURLESS_VALUES:
            continue
        if "var(--" in part or "currentcolor" in lowered:
            continue
        return False
    return True


def test_the_overlay_redefines_the_whole_palette_as_the_dark_scheme() -> None:
    """Every ``:root`` token is redefined on ``.hud-overlay`` at its dark value.

    FOUR ROUNDS OF THE SAME FAULT ENDED HERE. The overlay sits over a game
    pixel and does not follow the reader's scheme, so a descendant resolving a
    LIGHT colour paints it on a dark ground: measured at 1.04:1 on ``color``,
    then on ``border``, then on nested ``.hud-*`` rules, then on ``.facts dd``,
    ``h2`` and ``.lede``. Each repair enumerated the tokens some set of rules
    was known to read, and the next audit found a rule outside that set.

    SO THE REQUIREMENT IS DERIVED FROM THE SHEET'S OWN DECLARATION LIST rather
    than from any rule's reads. A token that exists must be redefined here,
    whoever reads it and whether or not anything reads it yet - which is the
    only boundary that does not move when someone writes a new rule.
    """
    css = read_asset(STYLESHEET)

    light_root = _block(css, ":root {")
    dark_root = _block(_block(css, "@media (prefers-color-scheme: dark) {"), ":root {")
    rules = css_rules(css)
    overlay = dict(rules).get(".hud-overlay", "")
    assert overlay, "there is no .hud-overlay rule to carry the redefinitions"

    declared = set(_VAR_DECLARE.findall(light_root))
    assert declared, "the sheet declares no palette; this arm would be vacuous"

    redefined = set(_VAR_DECLARE.findall(overlay))
    missing = tuple(sorted(declared - redefined))
    total = len(missing)
    assert total == 0, (
        f"{total} token(s) a descendant could resolve to a light value inside "
        f"the overlay, because the rule does not redefine them: {missing}"
    )

    dark_values = dict(_VAR_DECLARED_VALUE.findall(dark_root))
    overlay_values = dict(_VAR_DECLARED_VALUE.findall(overlay))
    drifted = tuple(
        sorted(
            name
            for name in declared
            if overlay_values.get(name, "").strip() != dark_values.get(name, "").strip()
        )
    )
    count = len(drifted)
    assert count == 0, (
        f"{count} token(s) redefined on the overlay differ from the dark :root "
        f"value they mirror, so the spelled copy has drifted: {drifted}"
    )

    # THE THREE BLOCKS ARE THE WHOLE COLOUR SURFACE, and that is what makes the
    # count above mean anything. A custom property declared on some other rule,
    # or a colour written as a literal with no token at all, reaches the overlay
    # subtree without passing through :root - so neither could be seen by a
    # check derived from :root, and both were demonstrated GREEN against the
    # first version of this arm.
    stray_tokens = tuple(
        sorted(
            f"{selector} declares {name}"
            for selector, body in rules
            if selector not in _COLOUR_BLOCKS
            for name in _VAR_DECLARE.findall(body)
        )
    )
    strays = len(stray_tokens)
    assert strays == 0, (
        f"{strays} custom propert(ies) declared outside the three colour blocks, "
        f"where the overlay cannot redefine them: {stray_tokens}"
    )

    # A COLOUR OUTSIDE THE BLOCKS MUST READ A TOKEN. The previous spelling of
    # this leg matched hex, `rgb(` and `hsl(` - three NOTATIONS - and was shown
    # green against `color: black`, `background: white`, `oklch(...)`,
    # `color-mix(...)` and `CanvasText`. A fourth pattern would have been beaten
    # by a fifth spelling, so the rule is inverted: the VALUE of a colour-bearing
    # declaration must either read a custom property or be one of the few
    # keywords that name no colour at all. That is closed over notations nobody
    # has invented yet - though NOT over how a declaration is spelled: an audit
    # defeated an earlier version of this leg with an optional trailing
    # semicolon, and the claim that it was closed was itself the fault.
    unsourced = tuple(
        sorted(
            f"{selector}: {prop}: {value.strip()}"
            for selector, body in rules
            if selector not in _COLOUR_BLOCKS
            for prop, value in _DECLARATIONS.findall(body)
            if prop.strip().lower() in _COLOUR_BEARING and not _token_sourced(value)
        )
    )
    unsourced_total = len(unsourced)
    assert unsourced_total == 0, (
        f"{unsourced_total} colour-bearing declaration(s) outside the three blocks "
        f"do not read a token, so the overlay cannot redefine them: {unsourced}"
    )

    # `color-scheme` IS NOT A CUSTOM PROPERTY, which is exactly why it escaped
    # a check derived from :root's declaration list. It selects the palette the
    # user agent paints scrollbars, form widgets and the caret from. The VALUE
    # is asserted and not merely the declaration's presence, because a presence
    # check passed `light` and `normal` when it was first written.
    scheme = re.search(r"color-scheme:\s*([^;]+);", overlay)
    assert scheme is not None, (
        "the overlay redefines every token and never declares color-scheme, so the "
        "user-agent-painted half still follows the reader's scheme"
    )
    declared_scheme = scheme.group(1).strip()
    assert declared_scheme == "dark", (
        f"the overlay declares color-scheme: {declared_scheme}, but it sits over a "
        f"game pixel and must pin the user-agent palette exactly as it pins the rest"
    )

    # `@property` DECLARES A CUSTOM PROPERTY THAT css_rules NEVER RETURNS, because
    # it drops every selector beginning with `@`. An `initial-value` there is a
    # colour no block owns and the overlay cannot redefine, invisible to both
    # legs above. The sheet uses none, and the cheapest way to keep it that way
    # is to say so.
    assert "@property" not in css, (
        "the sheet declares an @property custom property, whose initial-value is a "
        "colour outside the three blocks that .hud-overlay cannot redefine"
    )

    # WHAT THIS ARM CANNOT DO, STATED RATHER THAN IMPLIED. It reads characters.
    # It cannot resolve a cascade, cannot evaluate `light-dark()`, and cannot see
    # what any of this COMPUTES to - CONVENTIONS 13.3 asks for computed styles
    # and says a character read is not one. The rendered CS-600 audit discharges
    # that half; this arm only guarantees that every colour has a token to be
    # redefined through.


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


#: Every tag from :data:`_INTERACTIVE_TAGS` as a bare element name, plus
#: ``button`` - the one interactive element the page does admit. DERIVED from
#: that tuple rather than spelled again, so the arm above and the arms below
#: cannot come to disagree about what counts as a pointer target.
INJECTABLE_TAGS: Final = frozenset(
    {tag.lstrip("<").rstrip(" >") for tag in _INTERACTIVE_TAGS} | {"button"}
)

#: One ``document.createElement("tag")`` call, with the variable the new node is
#: bound to when there is one. A call whose argument is a VARIABLE - the generic
#: ``el``/``element``/``add`` helpers - does not match, which is exactly what
#: :func:`test_no_asset_names_an_interactive_tag_in_a_shape_this_module_cannot_read`
#: exists to catch.
_CREATE_CALL: Final = re.compile(
    r"""(?:(?P<name>[A-Za-z_$][\w$]*)\s*=\s*)?"""
    r"""document\.createElement\(\s*["'](?P<tag>[a-z]+)["']\s*\)"""
)

#: A bare tag-shaped string literal. Used to find an interactive tag name in a
#: position this module does not know how to resolve.
_TAG_LITERAL: Final = re.compile(r"""["']([a-z]+)["']""")

#: ``setAttribute("type", "button")``. The second legal place an interactive tag
#: name may appear in a script: it names an input TYPE, not a new element.
_TYPE_ATTRIBUTE: Final = re.compile(r"""setAttribute\(\s*["']type["']\s*,\s*["'][a-z]+["']\s*\)""")


def injected_controls(code: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Every interactive control the script CREATES, with the selectors that size it.

    WHY THIS IS DERIVED AND NOT A LIST OF CLASS NAMES. The solve bench's text
    input is built by a panel module at runtime and appears in no markup, so
    :func:`test_the_page_offers_exactly_one_kind_of_clickable_target` - which
    reads ``index.html`` - cannot see it, and the sizing arm above grades the
    ``button`` element selector alone. An arm naming ``.bench-input`` would grade
    exactly one control and go quietly out of date the moment a fifth panel
    injects a second one. So the set comes from the SCRIPTS, which own it.

    Resolution, in two shapes, both present in the assets today:

    - ``var input = document.createElement("input"); input.className = "x";``
      resolves to the class selector ``.x``.
    - ``var button = document.createElement("button");`` with no class resolves
      to the bare element selector ``button``.

    The class search is bounded to the text between this creation call and the
    next one, so a later node's class cannot be read as this one's. A node whose
    class is assigned after the next ``createElement`` resolves to its bare tag
    instead, which reddens the arm rather than passing quietly.

    A multi-class assignment yields one candidate per class and the caller
    requires ONE of them to carry the box - which is how CSS behaves.

    Args:
        code: One script's text with its block comments already removed by
            :func:`code_only`. The assets carry no ``//`` line comments at all -
            :func:`test_no_asset_references_a_remote_resource` is what keeps it
            that way - so no further stripping is needed here.

    Returns:
        One ``(tag, candidate selectors)`` pair per distinct control, in the
        order the script creates them.
    """
    found: list[tuple[str, tuple[str, ...]]] = []
    for match in _CREATE_CALL.finditer(code):
        tag = match.group("tag")
        if tag not in INJECTABLE_TAGS:
            continue
        candidates: tuple[str, ...] = (tag,)
        name = match.group("name")
        if name:
            window = code[match.end() :]
            following = window.find("document.createElement(")
            if following >= 0:
                window = window[:following]
            pattern = r"\b" + re.escape(name) + r"""\.className\s*=\s*["']([^"']+)["']"""
            assigned = re.search(pattern, window)
            if assigned:
                candidates = tuple("." + part for part in assigned.group(1).split())
        pair = (tag, candidates)
        if pair not in found:
            found.append(pair)
    return tuple(found)


def declarations_for(rules: tuple[tuple[str, str], ...], selector: str) -> str | None:
    """The body of the first rule whose selector LIST holds ``selector`` exactly.

    An exact match over the comma-split list, rather than a substring search:
    ``.bench-input`` is a substring of ``.bench-input:focus`` and of any
    descendant selector ending in it, and neither of those sizes the control.

    Args:
        rules: A :func:`css_rules` result.
        selector: One selector, spelled as the sheet spells it.

    Returns:
        The declarations, or ``None`` when no rule carries that selector alone.
    """
    for name, body in rules:
        if selector in tuple(part.strip() for part in name.split(",")):
            return body
    return None


def undersized_axes(declarations: str) -> tuple[str, ...]:
    """Which of the two axes this rule body fails to floor at the minimum.

    The same four questions the ``button`` arm above asks, in a form a caller can
    ask of any rule: is the axis declared, is it declared in px, and is the
    smallest px value it names at or above :data:`MIN_TARGET_PX`. That arm keeps
    its own copy deliberately - it is a passing guard and this slice widens
    coverage without touching it.

    Args:
        declarations: A rule body, as :func:`css_rules` returns one.

    Returns:
        One string per fault, empty when the rule declares a legal target box.
    """
    faults: list[str] = []
    for axis in ("min-width", "min-height"):
        line = next((part for part in declarations.split(";") if axis in part), None)
        if line is None:
            faults.append(f"{axis} undeclared")
            continue
        sizes = tuple(int(value) for value in _PX.findall(line))
        if not sizes:
            faults.append(f"{axis} is not declared in px")
        elif min(sizes) < MIN_TARGET_PX:
            faults.append(f"{axis} is {min(sizes)}px")
    return tuple(faults)


def test_the_injected_control_scan_reads_both_shapes_and_drops_a_div() -> None:
    """The resolver is proved on a sample before any arm relies on it.

    A resolver that silently returned nothing would make the arm below
    vacuously green, which is the exact shape this module exists to refuse.
    """
    sample = (
        'var wrap = document.createElement("div");\n'
        'wrap.className = "bench-field";\n'
        'var input = document.createElement("input");\n'
        'input.className = "bench-input";\n'
        'var button = document.createElement("button");\n'
        'button.setAttribute("type", "button");\n'
    )
    assert injected_controls(sample) == (
        ("input", (".bench-input",)),
        ("button", ("button",)),
    ), injected_controls(sample)


def test_the_target_box_reader_names_each_fault_it_claims() -> None:
    """:func:`undersized_axes` fires on all three faults and clears a legal box."""
    assert undersized_axes("min-width: 24px; min-height: 44px;") == ()
    assert undersized_axes("min-height: 44px;") == ("min-width undeclared",)
    assert undersized_axes("min-width: 100%; min-height: 44px;") == (
        "min-width is not declared in px",
    )
    assert undersized_axes("min-width: 8px; min-height: 44px;") == ("min-width is 8px",)


def test_every_control_a_script_injects_declares_the_target_box() -> None:
    """A control built at RUNTIME is held to the same minimum as a marked-up one.

    THIS IS THE ARM THE SOLVE BENCH HAD NONE OF. ``.bench-input`` declared a
    target box that no test read: the markup arm above scans ``index.html``, and
    a node a panel module creates appears in no markup, while the sizing arm
    above grades the ``button`` selector alone. So a stylesheet rule this project
    treats as a hit-target requirement was enforced by nothing.

    WHAT THIS ARM STILL CANNOT SAY. It grades DECLARED px, not computed style.
    No browser runs here, so a declared floor beaten by a later cascade or by a
    box-sizing interaction is out of its reach - see the section preamble above
    on what a source-level arm is worth.
    """
    rules = css_rules(read_asset(STYLESHEET))
    found: list[tuple[str, str, tuple[str, ...]]] = []
    for asset in (SCRIPT, *PANEL_MODULES):
        for tag, candidates in injected_controls(code_only(read_asset(asset))):
            found.append((asset, tag, candidates))

    assert found, "no script injects any interactive control - the scan found nothing"
    shapes = tuple(candidates[0][:1] for _, _, candidates in found)
    assert "." in shapes, f"no control resolved to a class selector: {found}"

    faults = []
    for asset, tag, candidates in found:
        graded = {
            selector: undersized_axes(body)
            for selector in candidates
            if (body := declarations_for(rules, selector)) is not None
        }
        if not any(result == () for result in graded.values()):
            faults.append((asset, tag, candidates, graded))
    assert not faults, f"injected controls with no legal target box: {faults}"


def test_no_asset_names_an_interactive_tag_in_a_shape_this_module_cannot_read() -> None:
    """An interactive tag name appears only where the arm above can resolve it.

    THIS IS THE ANTI-VACUITY HALF. The resolver reads
    ``document.createElement("input")`` and nothing else, so a future panel
    building its control through the generic ``el``/``element``/``add`` helper -
    ``el("input", "bench-input")`` - would create a pointer target the arm above
    never sees, and the coverage would be lost silently.

    The check is an ALLOWLIST of the two legal contexts, not a ban on a list of
    bad ones: a tag name may sit inside a ``createElement`` call or inside a
    ``setAttribute("type", ...)`` call, and anywhere else is a finding. A
    denylist would leak the moment a third shape arrived.
    """
    stray = []
    for asset in (SCRIPT, *PANEL_MODULES):
        code = code_only(read_asset(asset))
        legal = tuple(
            match.span()
            for pattern in (_CREATE_CALL, _TYPE_ATTRIBUTE)
            for match in pattern.finditer(code)
        )
        for match in _TAG_LITERAL.finditer(code):
            if match.group(1) not in INJECTABLE_TAGS:
                continue
            if any(start <= match.start() and match.end() <= end for start, end in legal):
                continue
            line = code.count("\n", 0, match.start()) + 1
            stray.append((asset, match.group(1), line))
    assert not stray, f"an interactive tag name sits where the scan cannot read it: {stray}"


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

    A ten-row table with six columns is the widest thing on the page. Letting
    it push the document sideways is the failure; giving its wrapper
    ``overflow-x: auto`` is the fix, and the markup has to actually use the
    wrapper for the rule to matter.

    CS-875 SWEEP: comments come out first. Both counts are presence claims, and
    one HTML comment holding ``<table`` beside another holding
    ``class="scroll-x"`` keeps them equal while the real markup has neither.
    """
    css = read_asset(STYLESHEET)
    markup = markup_only(read_asset(INDEX))

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

    CS-875 SIBLING - THE SLICE WAS NOT THE BLOCK. This arm used to search from
    ``} finally {`` to the END OF THE FILE, so moving both releases out past
    ``refresh()``'s closing brace - where a throw never reaches them - left it
    green. Worse, ``code.find`` returning ``-1`` sliced the last character of
    the file, which is a truthy string, so the "not where this arm expects it"
    guard could not fire. The ``finally`` is now brace-matched and its span
    ends where the block does.
    """
    code = code_only(read_asset(SCRIPT))
    mask = string_free(code)

    head = _REFRESH_HEAD.search(mask)
    assert head is not None, "refresh() is not declared where this arm can find it"
    body_first, body_last = block_span(mask, head.start())

    tail = _FINALLY_HEAD.search(mask, body_first, body_last)
    assert tail is not None, "refresh() releases its busy state outside a finally"

    first, last = block_span(mask, tail.start())
    release = code[first:last]
    assert 'removeAttribute("aria-disabled")' in release, (
        "aria-disabled is not withdrawn inside refresh()'s own finally block"
    )
    assert re.search(r"\w+\s*=\s*false", release), (
        "the re-entry flag is not lowered inside refresh()'s own finally block"
    )


# ---------------------------------------------------------------------------
# i2a. Reading the script as STRUCTURE rather than as a bag of characters
# ---------------------------------------------------------------------------
#
# CS-875. Four arms in this section graded a narrower population than they
# named, through two separate mechanisms. Both were demonstrated against the
# real app.js with `node --check` passing on the mutant, which is what makes
# each of them an edit that could really land.
#
#   A COMMENT IS NOT CODE. The arms read read_asset(SCRIPT) raw, so wrapping a
#   real statement in a /* */ block left every character they searched for
#   still sitting on disk. The measured 14641ms window in which the page has
#   no keyboard route came back, and the arm stayed green.
#
#   A SUBSTRING IS NOT A SEMANTICS, and code_only does not fix this half.
#   Changing === to !== in the focus guard inverts both branches, so a focused
#   box that stops overflowing gets removeAttribute called on it - verbatim the
#   blur regression this section exists to prevent - and the arm stayed green
#   because its real assertion was that the 22 characters of
#   "document.activeElement" appeared somewhere in the file.
#
#   AND INDENTATION IS NOT SCOPE. The repair BEFORE this one anchored on
#   column zero for a top-level statement and four spaces for one inside
#   refresh(). A four-space-indented call placed AFTER refresh()'s closing
#   brace satisfies that anchor and never runs in the finally.
#
# The three readers below answer the question those arms actually needed
# answered - WHERE does this call sit - by matching braces instead of counting
# spaces. Each is proved on a sample before anything relies on it, because a
# reader that silently returned nothing would make every arm below vacuously
# green, which is the exact shape this module exists to refuse.

#: The delimiters a JavaScript string literal may open with. A brace or a
#: keyword inside one is text, not structure.
_QUOTES = "\"'`"

#: The DOM's own name for the focused element, spelled once.
ACTIVE_ELEMENT: Final = "document.activeElement"

#: A ``tabindex`` grant AS A CALL rather than as the substring of one. The
#: leading dot is what makes it a method call on an element instead of five
#: tokens that happen to appear in that order.
_TABINDEX_GRANT = re.compile(r'\.setAttribute\(\s*"tabindex"\s*,\s*"(?P<value>-?\d+)"\s*\)')

#: The matching withdrawal.
_TABINDEX_WITHDRAWAL = re.compile(r'\.removeAttribute\(\s*"tabindex"\s*\)')

#: The role a focusable scroller is given, and the two withdrawals beside it.
_ROLE_GRANT = re.compile(r'\.setAttribute\(\s*"role"\s*,\s*"region"\s*\)')
_ROLE_WITHDRAWAL = re.compile(r'\.removeAttribute\(\s*"role"\s*\)')
_LABEL_WITHDRAWAL = re.compile(r'\.removeAttribute\(\s*"aria-label"\s*\)')

#: The read of the name stem out of the markup, capturing WHATEVER local name
#: it lands in so the arm can follow that name to the label it builds rather
#: than assuming what app.js happens to call it today.
_STEM_READ = re.compile(
    r"\bvar\s+(?P<stem>[A-Za-z_$][\w$]*)\s*=\s*"
    r'[A-Za-z_$][\w$]*\.getAttribute\(\s*"data-scroll-label"\s*\)'
)

#: A two-operand ``else if`` condition. Either side may be the focused-element
#: read, and THE OPERATOR IS CAPTURED RATHER THAN SPELLED IN: an arm that
#: hardcoded ``===`` would merely fail to match its own negation and then have
#: to guess what the absence meant, while one that searched for the left
#: operand alone was green against exactly that negation.
_BRANCH_GUARD = re.compile(
    r"\belse\s+if\s*\(\s*"
    r"(?P<left>document\.activeElement|[A-Za-z_$][\w$]*)\s*"
    r"(?P<operator>===|!==|==|!=)\s*"
    r"(?P<right>document\.activeElement|[A-Za-z_$][\w$]*)\s*"
    r"\)\s*\{"
)

#: The ``else`` that follows a branch, matched at the offset just past that
#: branch's own closing brace.
_ELSE_BLOCK = re.compile(r"\s*else\s*\{")

#: The three declarations and the two bare calls the structural arms locate.
#: ``syncScrollRegions`` is also passed by REFERENCE to addEventListener, which
#: is not a call - the trailing ``()`` and ``;`` are what tell the two apart.
_SYNC_HEAD = re.compile(r"\bfunction\s+syncScrollRegions\s*\(\s*\)\s*\{")
_SYNC_CALL = re.compile(r"(?<![\w$.])syncScrollRegions\s*\(\s*\)\s*;")
_REFRESH_HEAD = re.compile(r"\basync\s+function\s+refresh\s*\(\s*\)\s*\{")
_REFRESH_CALL = re.compile(r"(?<![\w$.])refresh\s*\(\s*\)\s*;")
_FINALLY_HEAD = re.compile(r"(?<![\w$])finally\s*\{")


def string_free(code: str) -> str:
    """``code`` with every string literal's body and every ``//`` comment blanked.

    THIS IS THE OTHER HALF OF :func:`code_only`. That one answers "is this
    prose or is it code". This one answers "is this brace structure or is it
    text", which is the question an arm asking WHERE a call sits has to settle
    before it can count anything. Length is preserved exactly - each blanked
    character becomes one space and newlines survive - so an offset into the
    result indexes the same character of the input, and a span measured on the
    result may be sliced out of the input.

    Block comments are NOT handled here; run :func:`code_only` first. A regular
    expression literal is not recognised either. ``app.js`` contains none, and
    an edit that adds one has to revisit this rather than assume it copes.

    Args:
        code: The script with its block comments already removed.

    Returns:
        The same text at the same length, with string bodies and line comments
        replaced by spaces. The quote characters themselves are kept, so the
        token structure of a call is still visible.
    """
    out = list(code)
    index = 0
    while index < len(code):
        char = code[index]
        if char in _QUOTES:
            index += 1
            while index < len(code) and code[index] != char:
                out[index] = " "
                if code[index] == "\\" and index + 1 < len(code):
                    index += 1
                    out[index] = " "
                index += 1
            index += 1
        elif code.startswith("//", index):
            while index < len(code) and code[index] != "\n":
                out[index] = " "
                index += 1
        else:
            index += 1
    return "".join(out)


def statement_depth(mask: str, at: int) -> int:
    """How many blocks stand open at offset ``at``.

    Args:
        mask: A :func:`string_free` result, so a brace inside a string cannot
            be mistaken for a block delimiter.
        at: An offset into that text.

    Returns:
        Zero at the file's top level, one inside a single block, and so on.
    """
    return mask.count("{", 0, at) - mask.count("}", 0, at)


def block_span(mask: str, start: int) -> tuple[int, int]:
    """The half-open span INSIDE the first block that opens at or after ``start``.

    A SUBSTRING IS NOT A CALL SITE AND INDENTATION IS NOT SCOPE. An arm meaning
    "this call is inside that block" has to find the block's own closing brace,
    because four spaces of indentation are satisfied just as well by a line
    placed after the block has ended.

    Args:
        mask: A :func:`string_free` result.
        start: Where to begin looking for the opening brace.

    Returns:
        ``(first, last)`` - the offset just past the opening brace, and the
        offset OF the matching closing brace.

    Raises:
        ValueError: If no block opens at or after ``start``, or if the one that
            does is never closed.
    """
    opened = mask.find("{", start)
    if opened < 0:
        raise ValueError("no block opens at or after this offset")
    depth = 0
    for index in range(opened, len(mask)):
        if mask[index] == "{":
            depth += 1
        elif mask[index] == "}":
            depth -= 1
            if depth == 0:
                return opened + 1, index
    raise ValueError("the block that opens here is never closed")


def test_the_string_blanker_hides_text_and_keeps_structure() -> None:
    """A brace inside a string stops counting; the code around it does not."""
    sample = 'var a = "} not a brace {"; if (b) { c(); } // } nor is this\n'
    mask = string_free(sample)
    assert len(mask) == len(sample), (len(mask), len(sample))
    assert mask.count("{") == 1, mask
    assert mask.count("}") == 1, mask
    assert "if (b)" in mask, mask
    assert "not a brace" not in mask, mask
    assert "nor is this" not in mask, mask


def test_the_string_blanker_survives_an_escaped_delimiter() -> None:
    """An escaped quote does not end the literal it sits inside."""
    sample = 'var a = "he said \\" { "; d();'
    mask = string_free(sample)
    assert mask.count("{") == 0, mask
    assert "d();" in mask, mask


def test_the_block_finder_returns_the_matching_brace_not_the_first_one() -> None:
    """A nested block does not close the one containing it."""
    sample = "f() { a(); { b(); } c(); } d();"
    first, last = block_span(sample, 0)
    body = sample[first:last]
    assert "c();" in body, body
    assert "d();" not in body, body


def test_the_block_finder_refuses_a_block_that_is_never_closed() -> None:
    """An unbalanced file raises rather than returning a span that means nothing."""
    with pytest.raises(ValueError, match="never closed"):
        block_span("f() { a();", 0)


def test_the_depth_reader_counts_the_blocks_standing_open() -> None:
    """Top level is zero and each unclosed brace is one more."""
    sample = "a(); { b(); { c(); } } d();"
    assert statement_depth(sample, sample.index("a();")) == 0, sample
    assert statement_depth(sample, sample.index("b();")) == 1, sample
    nested = 2
    assert statement_depth(sample, sample.index("c();")) == nested, sample
    assert statement_depth(sample, sample.index("d();")) == 0, sample


def test_the_call_patterns_tell_a_call_from_a_reference() -> None:
    """``addEventListener("resize", syncScrollRegions)`` is not a call to it."""
    reference = 'window.addEventListener("resize", syncScrollRegions);'
    assert _SYNC_CALL.search(reference) is None, reference
    assert _SYNC_CALL.search("syncScrollRegions();") is not None
    assert _REFRESH_CALL.search('byId("refresh").addEventListener("click", refresh);') is None
    assert _REFRESH_CALL.search("refresh();") is not None


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

    THE STOP IS NOW DERIVED AND SO THIS ARM MOVED WITH IT (second CS-600 audit).
    It used to require ``tabindex="0"`` on every scroller IN THE MARKUP, and the
    audit measured that unconditional claim false twice: the World scroller
    reports ``scrollWidth === clientWidth`` at 1574, 375 and 320px - it never
    scrolls at any tested width - and it kept its stop when a failed
    ``/api/world`` hid its table, leaving a 1.33px empty box that took focus and
    announced itself as a scrollable region of world counts. ``app.js`` now sets
    and removes the three attributes from the measured overflow.

    SO WHAT IS GRADED HERE IS THE PROPERTY THAT SURVIVED: no ``tabindex`` is
    written into the markup at all, every scroller is declared where a table is,
    and the only thing that may ever grant one is the sync function - which is
    required to grant ``0`` and nothing else. The RUNTIME half - that the stop
    appears exactly while the box overflows - is measured in the browser during
    the audit, because no reading of this file can establish it.

    CS-875 - THE SCRIPT HALF READ THE RAW FILE AND MATCHED A FRAGMENT. Both
    faults were demonstrated. Wrapping the real grant in a ``/* */`` block left
    the searched-for characters on disk, so ``re.findall`` still found them and
    the arm stayed green while no box could be reached from the keyboard; and
    "the only thing that may ever grant one is the sync function" was asserted
    NOWHERE - the pattern matched wherever in the file it appeared. The grant is
    now sought in :func:`code_only` output, as a ``.setAttribute(...)`` call,
    and its offset is required to fall inside ``syncScrollRegions``'s own
    brace-matched body.
    """
    markup = markup_only(read_asset(INDEX))
    assert not re.findall(r'tabindex="(-?\d+)"', markup), (
        "a tabindex is declared in the markup; the stop is derived from measured "
        "overflow in app.js, and a static one is the unconditional claim the audit "
        "measured false"
    )

    scrollers = re.findall(r"<div class=\"scroll-x\"[^>]*>", markup)
    assert len(scrollers) == markup.count("<table"), "a table has no scroller"

    code = code_only(read_asset(SCRIPT))
    mask = string_free(code)

    head = _SYNC_HEAD.search(mask)
    assert head is not None, "app.js declares no syncScrollRegions function to grade"
    sync_first, sync_last = block_span(mask, head.start())

    grants = tuple(_TABINDEX_GRANT.finditer(code))
    assert grants, "nothing in app.js ever grants a tab stop, so no scroller can be reached"
    wrong = tuple(found.group("value") for found in grants if found.group("value") != "0")
    assert not wrong, (
        f"tabindex values that are not 0: {wrong}; a positive value invents a second "
        "ordering that disagrees with the visual one"
    )
    stray = tuple(found.group(0) for found in grants if not sync_first <= found.start() < sync_last)
    assert not stray, (
        f"{len(stray)} tab stop(s) granted outside syncScrollRegions: {stray}; a grant "
        "the sync function cannot see is a stop that nothing ever withdraws"
    )
    withdrawn = _TABINDEX_WITHDRAWAL.search(code, sync_first, sync_last) is not None
    assert withdrawn, (
        "syncScrollRegions grants a tab stop and never withdraws one, so a box that "
        "stops overflowing keeps a stop it has not earned"
    )


def test_every_focusable_scroller_carries_its_own_accessible_name() -> None:
    """Each scroller declares a role and a label, and no two labels are equal.

    Focus landing on an unnamed box announces nothing, which is a stop a
    keyboard reader cannot account for. Two boxes sharing a name is the same
    fault one step later: the second stop is indistinguishable from the first.

    THE NAME IS NOW BUILT AT RUNTIME FROM ``data-scroll-label`` (second CS-600
    audit), so the uniqueness that matters is the uniqueness of that attribute.
    The audit's MUST-FIX was that the static ``aria-label`` asserted "scrolls
    sideways" on a box measured never to scroll at any tested width; the suffix
    is now appended only where the overflow is real, which is why the stem is
    what this file can grade and the whole name is not.

    CS-875 - THE SCRIPT HALF READ THE RAW FILE, so a ``/* */`` block holding any
    of these four fragments satisfied the arm while the code did none of it. It
    now reads :func:`code_only` output and matches CALLS. The last assertion
    also stopped being a bare mention of ``data-scroll-label``: the stem's read
    is located, WHATEVER local name it lands in is captured, and that name is
    then required to be the one an ``aria-label`` is built from - so a label
    rebuilt from a literal is a failure rather than a silent lie to a reader.
    """
    markup = markup_only(read_asset(INDEX))
    scrollers = re.findall(r"<div class=\"scroll-x\"[^>]*>", markup)
    assert scrollers, "no scroller found"

    assert not re.search(r'aria-label="[^"]*"', markup), (
        "an aria-label is declared in the markup; the name is built in app.js from "
        "data-scroll-label so it can state the scroll claim only where it is true"
    )

    labels = []
    for scroller in scrollers:
        found = re.search(r'data-scroll-label="([^"]+)"', scroller)
        assert found is not None, f"scroller carries no name stem: {scroller}"
        labels.append(found.group(1))
    assert len(set(labels)) == len(labels), f"two scrollers share a name: {labels}"

    code = code_only(read_asset(SCRIPT))
    named = _ROLE_GRANT.search(code) is not None
    assert named, "nothing gives a focusable scroller a role, so a stop announces an unnamed box"
    unroled = _ROLE_WITHDRAWAL.search(code) is not None
    assert unroled, "a box that stops overflowing keeps a role it has not earned"
    unnamed = _LABEL_WITHDRAWAL.search(code) is not None
    assert unnamed, "a box that stops overflowing keeps a name it has not earned"

    read = _STEM_READ.search(code)
    assert read is not None, (
        "app.js never calls getAttribute for data-scroll-label, so the markup's name "
        "stems reach nothing"
    )
    stem = read.group("stem")
    built = re.search(r'\.setAttribute\(\s*"aria-label"\s*,\s*' + re.escape(stem) + r"\b", code)
    assert built is not None, (
        f"the stem is read into {stem!r} and no aria-label is built from it, so the "
        "name a reader hears is not the one the markup declares"
    )


def test_a_scroller_losing_its_overflow_does_not_take_focus_with_it() -> None:
    """The stop is never removed from under a reader standing on it.

    THE FIRST DERIVED-AFFORDANCE BUILD DID EXACTLY THAT, and a re-audit measured
    it: focus the scroller at 375px, widen to 1574, and ``removeAttribute`` on
    the focused element blurred it - ``activeElement`` finished at ``BODY``, only
    blur and focusout fired, and nothing was announced. IT IS THE SAME FAULT
    ``refresh()`` DOCUMENTS FOR ``button.disabled`` in the same file, reached
    through a different door, which is why the guard is here and not left to the
    next audit to find again.

    Behaviourally confirmed in the repair slice rather than here, since no
    reading of this file can establish it: at 1574 with the box focused,
    ``activeElement`` stayed on the scroller, the label dropped its scroll claim
    to "Endpoint routes", and moving focus to the button then withdrew tabindex,
    role and aria-label together.

    WHAT THIS FILE CAN GRADE is that the removal branch is reachable only when
    the box is not the active element - and CS-875 is why it now grades that
    rather than something adjacent to it. The arm used to assert that the 22
    characters of ``document.activeElement`` appeared somewhere in the file.
    Changing ``===`` to ``!==`` in the guard passes ``node --check``, inverts
    both branches, and calls ``removeAttribute`` on a focused box - which is
    verbatim the regression recounted above - and the arm stayed green, because
    those 22 characters were still exactly where they had always been.

    SO THE COMPARISON IS NOW READ AS A COMPARISON. The operator is captured and
    required to be an identity test; the branch it guards is brace-matched and
    required to strip nothing; the ``else`` beside it is brace-matched and
    required to strip all three attributes; and the box those removals name is
    the one the condition named, not one this file assumed.
    """
    code = code_only(read_asset(SCRIPT))
    mask = string_free(code)

    guards = tuple(
        found
        for found in _BRANCH_GUARD.finditer(mask)
        if ACTIVE_ELEMENT in (found.group("left"), found.group("right"))
    )
    assert guards, (
        "no branch in app.js is guarded on document.activeElement, so a box losing "
        "its overflow strips its own tab stop and drops the reader to the document"
    )
    assert len(guards) == 1, (
        f"{len(guards)} focus guards; this arm grades one and would wave a second one "
        "through ungraded, so extend it rather than relaxing the count"
    )

    guard = guards[0]
    operator = guard.group("operator")
    assert operator == "===", (
        f"the focus guard compares document.activeElement with {operator!r}; only an "
        "identity test holds the stop for the box that HAS focus, and the negation "
        "hands the held branch to every box that does not"
    )

    left, right = guard.group("left"), guard.group("right")
    subject = left if right == ACTIVE_ELEMENT else right
    held_first, held_last = block_span(mask, guard.start())
    held = code[held_first:held_last]
    assert "removeAttribute" not in held, (
        f"the branch taken while {subject} holds focus removes an attribute from it, "
        "and removing tabindex from the focused element blurs it - which is the "
        "measured regression this guard exists to stop"
    )
    assert f'{subject}.addEventListener("blur"' in held, (
        "the stop is held for a focused box and never withdrawn when focus leaves, "
        "so a box that stopped overflowing keeps a stop it has not earned"
    )

    otherwise = _ELSE_BLOCK.match(mask, held_last + 1)
    assert otherwise is not None, (
        "the focus guard has no else branch, so a box that stops overflowing without "
        "holding focus keeps the stop, the role and the name it has not earned"
    )
    strip_first, strip_last = block_span(mask, otherwise.start())
    stripping = code[strip_first:strip_last]
    kept = tuple(
        name
        for name in ("tabindex", "role", "aria-label")
        if f'{subject}.removeAttribute("{name}")' not in stripping
    )
    assert not kept, (
        f"the unfocused branch never withdraws {kept} from {subject}, so an attribute "
        "outlives the overflow that earned it"
    )


def test_the_tab_stop_is_derived_before_the_first_fetch_resolves() -> None:
    """A keyboard route at first paint, not after five probes.

    MEASURED REGRESSION, caught by a re-audit rather than by this file: deriving
    the stop only at the end of ``refresh()`` left the endpoint scroller - which
    overflows at 375px on its headings alone - with no keyboard route for
    14641ms while the probes resolved. The static markup it replaced carried the
    stop from first paint, so the derived version was strictly worse for that
    window.

    THE SECOND HALF IS THE ``finally``. A throw in any renderer must not leave
    the page permanently without a route to its scrollers while the same
    ``finally`` cheerfully hands the button back.

    NEITHER ASSERTION IS ANCHORED ON TEXT ANY MORE, AND CS-875 IS WHY. The
    first draft searched for the bare call in a slice of the file and passed
    against both deletions. The second anchored on indentation - column zero
    for a top-level statement, four spaces for one inside ``refresh()`` - and
    two mutants beat that too, both of them passing ``node --check``. Wrapping
    the column-zero call in a ``/* */`` block leaves a newline in front of an
    unindented copy of itself, so the anchor still matched and the 14641ms
    no-keyboard-route window came back green. And four spaces is not scope: an
    indented call placed AFTER ``refresh()``'s closing brace satisfies the
    ``finally`` half while the post-render sync never runs.

    SO BOTH HALVES ARE READ AS STRUCTURE NOW. Comments come out first, string
    bodies are blanked so a brace inside one cannot be taken for a block, and a
    call is placed by how many blocks stand open above it. The bootstrap must
    be a call at depth zero occurring BEFORE the first top-level ``refresh()``,
    and the post-render sync must be a direct statement of the brace-matched
    block belonging to ``refresh()``'s own ``finally``.
    """
    code = code_only(read_asset(SCRIPT))
    mask = string_free(code)

    boots = tuple(
        found.start()
        for found in _SYNC_CALL.finditer(mask)
        if statement_depth(mask, found.start()) == 0
    )
    paints = tuple(
        found.start()
        for found in _REFRESH_CALL.finditer(mask)
        if statement_depth(mask, found.start()) == 0
    )
    assert paints, "nothing calls refresh() at top level, so the page never paints at all"
    assert any(at < paints[0] for at in boots), (
        "no top-level syncScrollRegions() call runs before the first top-level "
        "refresh(), so an overflowing scroller has no keyboard route until every "
        "probe resolves"
    )

    head = _REFRESH_HEAD.search(mask)
    assert head is not None, "refresh() is not declared where this arm can find it"
    body_first, body_last = block_span(mask, head.start())

    tail = _FINALLY_HEAD.search(mask, body_first, body_last)
    assert tail is not None, "refresh() has no finally, so a throw latches the page"

    finally_first, finally_last = block_span(mask, tail.start())
    depth = statement_depth(mask, finally_first)
    synced = tuple(
        found.start()
        for found in _SYNC_CALL.finditer(mask, finally_first, finally_last)
        if statement_depth(mask, found.start()) == depth
    )
    assert synced, (
        "the post-render sync is not a statement of refresh()'s finally block, so a "
        "throw in a renderer leaves the page with no keyboard route to its scrollers"
    )


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
    elements past the viewport edge at 375px - 5 of them structural boxes
    overhanging by 0.333px of sub-pixel rounding - and found all 57 real ones
    inside a working scroller. What it did do was swallow the signal - a scrollbar is the only
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


#: Right-aligned selectors that name no table cell, and so have no header to
#: pair with. A HUD figure is a stacked numeric readout inside a card: it lines
#: its digits up against the card's right edge, and the thing naming it sits
#: beside it rather than above it. The list is EXPLICIT rather than a pattern
#: so that a new right-aligned rule has to be added here on purpose - the arm
#: below still refuses any right-aligned selector that is neither paired nor
#: named, which is the ratchet the original spelling provided.
_RIGHT_ALIGNED_NON_COLUMN: Final = (".hud-figure",)


def test_a_numeric_column_header_shares_the_alignment_of_its_cells() -> None:
    """Whatever right-aligns ``td.count`` right-aligns ``th.count`` too.

    ``td.count`` was right-aligned so the ones line up under the ones, while its
    header inherited the left alignment every other cell takes - which left the
    word naming the column at the opposite end of it from the numbers. The
    header carries the same class as the cells, so the pairing is one token in
    the markup rather than two rules agreeing by coincidence.

    A SELECTOR THAT NAMES NO TABLE CELL IS OUT OF THIS INVARIANT'S SCOPE, and
    is admitted only by being listed in ``_RIGHT_ALIGNED_NON_COLUMN``. The arm
    checks those really do name no cell, so the list cannot be used to excuse a
    column from the pairing it does owe.
    """
    rules = css_rules(read_asset(STYLESHEET))
    aligned = tuple(selector for selector, body in rules if "text-align: right" in body)
    assert aligned, "nothing on the page is right-aligned"

    stale = tuple(name for name in _RIGHT_ALIGNED_NON_COLUMN if name not in aligned)
    assert not stale, f"named as right-aligned but no longer is: {stale}"

    for selector in aligned:
        if selector in _RIGHT_ALIGNED_NON_COLUMN:
            names_a_cell = "td" in selector or "th" in selector
            assert not names_a_cell, (
                f"{selector} is excused from the header pairing but names a table cell"
            )
            continue
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
# j. The page's own content: ten rows, and the blocked-by id as text
# ---------------------------------------------------------------------------


def test_the_script_names_every_published_route_template() -> None:
    """All ten of ``health.ENDPOINT_TEMPLATES`` appear in the row table.

    Read from the endpoint module rather than restated here, so a tenth route
    landing in BOOTSTRAP.md section 7.1 turns this red instead of leaving the
    page one row short and silent.

    CS-875 SWEEP: comments come out first. ``app.js`` opens with a comment that
    names the ten routes in section order, so a template deleted from the row
    table was still findable in the prose describing it.
    """
    code = code_only(read_asset(SCRIPT))
    expected = len(health.ENDPOINT_TEMPLATES)
    missing = tuple(name for name in health.ENDPOINT_TEMPLATES if f'"{name}"' not in code)
    total = len(missing)
    assert total == 0, f"{total} of {expected} route templates absent from app.js: {missing}"


def test_the_script_gives_each_route_the_method_its_owner_publishes() -> None:
    """Every method the page prints is the one the endpoint module registers.

    The five unbacked routes carry their verb in ``pending.UNBACKED``; the two
    solver routes carry theirs in ``solve.METHOD_POST``. Both are read here.
    A page that printed GET beside ``/api/solve`` would be telling an operator
    to make a request the server refuses.

    CS-875 SWEEP: comments come out first, so the row this reads is a row of
    the table rather than an example of one written into a comment.
    """
    code = code_only(read_asset(SCRIPT))
    expected = {template: method for method, template in pending.UNBACKED} | {
        solve.SOLVE_ENDPOINT: solve.METHOD_POST,
        solve.OPTIMIZE_ENDPOINT: solve.METHOD_POST,
        health.ENDPOINT: "GET",
        WORLD_ENDPOINT: "GET",
        REGISTRY_ENDPOINT: "GET",
        MAP_ENDPOINT: "GET",
    }
    assert len(expected) == len(health.ENDPOINT_TEMPLATES), sorted(expected)

    entries = dict(re.findall(r'template: "([^"]+)", method: "([A-Z]+)"', code))
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

    The 501 rows are the deliverable, not a gap to disguise: five of ten routes
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
    """The header line and the badges read the health body's own keys.

    CS-875 SWEEP: comments come out first, because a key quoted in a comment is
    not a key the page reads.
    """
    code = code_only(read_asset(SCRIPT))
    absent = tuple(key for key in health.DATA_KEYS if f'"{key}"' not in code)
    total = len(absent)
    assert total == 0, f"{total} health key(s) the page never reads: {absent}"


def test_the_page_shows_the_masked_token_and_the_world_scalars() -> None:
    """Every top-level ``/api/world`` key is read, including the counts.

    CS-875 SWEEP: comments come out first, because a key quoted in a comment is
    not a key the page reads.
    """
    code = code_only(read_asset(SCRIPT))
    absent = tuple(key for key in ("world", "counts", "unknown_classes") if f'"{key}"' not in code)
    total = len(absent)
    assert total == 0, f"{total} world key(s) the page never reads: {absent}"

    scalars = ("header_version", "save_version", "build_changelist", "body_offset")
    unread = tuple(key for key in scalars if f'"{key}"' not in code)
    assert not unread, f"version scalars the page never reads: {unread}"


#: A ``fetch`` call AS A CALL. The lookbehind separates the call from the same
#: six characters appearing inside a longer identifier or after a dot, which is
#: the distinction :data:`_SINKS` above already had to make for ``.innerHTML``.
_FETCH_CALL = re.compile(r"(?<![\w$.])fetch\s*\(")

#: The verb an options object names. Read out of THAT OBJECT and never out of a
#: window of characters following the call, because the arm this feeds counts
#: calls and a window cannot say which call it landed in.
_OPTIONS_METHOD = re.compile(r'\bmethod\s*:\s*"([A-Za-z]+)"')

#: A request body in an options object, spelled as a KEY - the name followed by
#: a colon - so a local variable named ``body`` or a ``result.body`` read cannot
#: be mistaken for one.
_OPTIONS_BODY = re.compile(r"(?<![\w$.-])body\s*:")


class FetchCall(NamedTuple):
    """One ``fetch`` call site, split into the three things this section asks about.

    Attributes:
        target: The first argument exactly as written, so an arm may assert what
            path a call asks for rather than only what verb it uses.
        method: The verb its options name, or ``None`` where they name none.
        sends_body: Whether its options carry a request body at all.
    """

    target: str
    method: str | None
    sends_body: bool


def call_span(mask: str, start: int) -> tuple[int, int]:
    """The half-open span INSIDE the first argument list opening at or after ``start``.

    The paren-matching sibling of :func:`block_span`, and it exists for the same
    reason: a fixed-width window of characters after ``fetch(`` is not a call.
    The window the arm below replaced was 200 characters wide, which is both
    longer than the whole of one call here and shorter than the options object
    of a call somebody might write next.

    Args:
        mask: A :func:`string_free` result, so a parenthesis inside a string
            literal cannot be mistaken for a delimiter.
        start: Where to begin looking for the opening parenthesis.

    Returns:
        ``(first, last)`` - the offset just past the opening parenthesis, and
        the offset OF the matching closing one.

    Raises:
        ValueError: If no call opens at or after ``start``, or if the one that
            does is never closed.
    """
    opened = mask.find("(", start)
    if opened < 0:
        raise ValueError("no call opens at or after this offset")
    depth = 0
    for index in range(opened, len(mask)):
        if mask[index] == "(":
            depth += 1
        elif mask[index] == ")":
            depth -= 1
            if depth == 0:
                return opened + 1, index
    raise ValueError("the call that opens here is never closed")


def fetch_calls(code: str) -> tuple[FetchCall, ...]:
    """Every ``fetch`` call in the script, in file order.

    Args:
        code: The script with its block comments already removed.

    Returns:
        One :class:`FetchCall` per call site.
    """
    mask = string_free(code)
    calls: list[FetchCall] = []
    for match in _FETCH_CALL.finditer(mask):
        first, last = call_span(mask, match.end() - 1)
        depth = 0
        cut = last
        for index in range(first, last):
            char = mask[index]
            if char in "([{":
                depth += 1
            elif char in ")]}":
                depth -= 1
            elif char == "," and depth == 0:
                cut = index
                break
        options = code[cut + 1 : last] if cut < last else ""
        named = _OPTIONS_METHOD.search(options)
        calls.append(
            FetchCall(
                target=code[first:cut].strip(),
                method=named.group(1) if named else None,
                sends_body=_OPTIONS_BODY.search(options) is not None,
            )
        )
    return tuple(calls)


def test_the_page_issues_exactly_one_post_and_no_form() -> None:
    """One non-GET request, to ``/api/solve``, with no body and still no form.

    THE SUCCESSOR TO ``test_the_page_issues_no_post_and_no_form``, WHICH WAS
    RIGHT UNTIL THE OPERATOR RULED OTHERWISE. That arm asserted the page named
    POST nowhere outside its route table and that every fetch it issued was a
    GET - true of the walking skeleton and false of a page carrying a solve
    bench. CS-962 does not relax the claim, it re-aims it: the question a CSRF
    reader needs answered is not "does this page ever POST" but "how many
    state-changing requests can it make, where do they go, and what do they
    carry". A count of ONE, pinned to ONE path, is a stronger statement than an
    absence that any later slice could quietly spend.

    AND THE PARAMETERS RIDE IN THE QUERY STRING, WHICH IS WHY THE BODY LEG IS
    HERE. ``clockspeed/surface/server.py`` parses the query and reads the
    request body nowhere at all, so a body would be ignored on arrival - and an
    unread body on a kept-alive HTTP/1.1 connection is the classic desync. A
    fetch with no ``body`` key sends ``Content-Length: 0``, which is safe; this
    arm is what keeps it that way.
    """
    code = code_only(read_asset(SCRIPT))
    markup = read_asset(INDEX)
    assert "<form" not in markup, "the page carries a form"

    table = re.search(r"var ROUTES = \[[\s\S]*?\n\];", code)
    assert table is not None, "the route table is not where this arm expects it"

    verbs = re.findall(r"method: \"([A-Z]+)\"", table.group(0))
    posts = tuple(verb for verb in verbs if verb == "POST")
    expected_posts = 3
    assert len(posts) == expected_posts, f"the route table names {len(posts)} POST verb(s)"

    calls = fetch_calls(code)
    assert calls, "no fetch call parsed at all, so this arm grades nothing"

    unnamed = tuple(call.target for call in calls if call.method is None)
    assert not unnamed, f"a fetch names no method at all: {unnamed}"

    non_get = tuple(call for call in calls if call.method != "GET")
    total = len(non_get)
    assert total == 1, (
        f"the page issues {total} non-GET fetch(es) rather than exactly one: "
        f"{tuple((call.method, call.target) for call in non_get)}"
    )

    only = non_get[0]
    assert only.method == "POST", f"the one non-GET fetch issues {only.method}"
    assert only.target.startswith('"/api/solve?'), (
        f"the one non-GET fetch does not ask for /api/solve with a query string: {only.target}"
    )

    carried = tuple(f"{call.method} {call.target}" for call in calls if call.sends_body)
    assert not carried, f"a fetch carries a request body the server never reads: {carried}"


def test_the_request_detector_fires_on_a_planted_second_call_and_on_a_body() -> None:
    """Both legs of the arm above are proved able to fire, on real edits.

    A detector that parsed nothing would report zero non-GET calls and zero
    bodies, and the arm above would then be green over a page that POSTs to
    anywhere it likes. Each leg is therefore run once against the shipped text,
    where the count is known, and once against that text with the banned edit
    PLANTED, where it must move.
    """
    clean = code_only(read_asset(SCRIPT))
    parsed = fetch_calls(clean)
    minimum_calls = 2
    assert len(parsed) >= minimum_calls, (
        f"the detector read {len(parsed)} fetch call(s); the script issues more"
    )
    assert len(tuple(call for call in parsed if call.method != "GET")) == 1

    planted = clean + (
        "\nfunction plantedSecond() {\n"
        '  return fetch("/api/optimize?targets=x", { method: "POST", cache: "no-store" });\n'
        "}\n"
    )
    after = tuple(call for call in fetch_calls(planted) if call.method != "GET")
    expected_after = 2
    assert len(after) == expected_after, (
        f"the detector saw {len(after)} non-GET call(s) after planting a second one"
    )

    bodied = clean + (
        "\nfunction plantedBody() {\n"
        '  return fetch("/api/solve?targets=x", { method: "POST", body: "targets=x" });\n'
        "}\n"
    )
    seen = tuple(call for call in fetch_calls(bodied) if call.sends_body)
    assert len(seen) == 1, f"the detector saw {len(seen)} body-carrying call(s) after planting one"


# ---------------------------------------------------------------------------
# k. Nothing in this slice claims a port from the reserved band
# ---------------------------------------------------------------------------


#: The slice files that are not shipped assets. Named here once so the two
#: sweeps below cannot disagree about what "this slice" covers, and so a file
#: added to the slice is added in one place.
NON_ASSET_SLICE_FILES: Final = (
    "test_web_assets.py",
    "test_panel_seam.py",
    "audit_harness.py",
)


def slice_files() -> tuple[Path, ...]:
    """Every file this slice ships or grades with, assets first.

    Returns:
        The shipped assets followed by this slice's own test modules.
    """
    here = Path(__file__).resolve().parent
    return tuple(WEB_DIR / name for name in ASSET_NAMES) + tuple(
        here / name for name in NON_ASSET_SLICE_FILES
    )


def test_no_file_in_this_slice_names_a_reserved_dashboard_port() -> None:
    """The band belongs to ``config/ports.json``; this slice binds port zero."""
    files = slice_files()
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


def test_the_harness_releases_its_port_and_a_restart_binds_a_fresh_one() -> None:
    """The harness lifecycle, driven directly rather than through the fixture.

    THE MODULE FIXTURE STARTS IT ONCE, so every other arm here shares a single
    running instance and none of them can grade ``stop``. A harness that bound
    a port and never released it would leave a listener behind after the suite,
    and the next run would collide with it - so "stop releases the port" is a
    claim this module makes and, until this arm, graded nowhere.

    It is also the only arm that CALLS into ``tests/surface/audit_harness.py``
    from a population member rather than from a fixture, which is what
    ``tests/test_liveness.py`` reads when it asks whether anything in the suite
    grades that module. A detector reached only through a fixture is reached by
    nothing the call graph can see.
    """
    first = audit_harness.AuditHarness()
    first.start()
    try:
        first_port = first.port
        code, body, _ = get(first_port, "/")
        assert code == HTTP_OK, f"the harness did not serve its own page: {code}"
        served = len(body)
        assert served > 0, "the harness served an empty page"
    finally:
        first.stop()

    probe = socket.socket()
    probe.settimeout(SOCKET_PROBE_SECONDS)
    try:
        reachable = probe.connect_ex(("127.0.0.1", first_port))
    finally:
        probe.close()
    assert reachable != 0, f"the harness left port {first_port} listening after stop"

    second = audit_harness.AuditHarness()
    second.start()
    try:
        second_port = second.port
        assert second_port > 0, "the restarted harness reports no bound port"
        assert not PORT_BAND_FIRST <= second_port <= PORT_BAND_LAST, (
            f"the restarted harness bound inside the reserved band: {second_port}"
        )
        code, body, _ = get(second_port, "/")
        assert code == HTTP_OK, f"the restarted harness did not serve its page: {code}"
        assert len(body) == served, "the restarted harness served a different page"
    finally:
        second.stop()


def test_the_harness_serves_every_real_asset_file(
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
    """Same top-level keys, same data keys, same ten-entry liveness map."""
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
    """Every slice file is LF-terminated, asserted on raw bytes.

    ``write_text`` converts LF to CRLF on Windows and ``read_text`` hides it, so
    a byte count is the only reading that sees the fault. Git normalises the
    blob and reports the tree clean while the working tree violates the rule.
    """
    files = slice_files()
    expected = len(ASSET_NAMES) + len(NON_ASSET_SLICE_FILES)
    assert len(files) == expected, files

    findings = {
        path.name: path.read_bytes().count(b"\r")
        for path in files
        if path.read_bytes().count(b"\r") > 0
    }
    total = len(findings)
    assert total == 0, f"carriage returns in {total} slice file(s): {findings}"
