"""CS-918 - does the dashboard actually run. A SCRIPT, not an opinion.

THE DEFECT THIS MODULE CLOSES. "Does the dashboard actually run" has been
relitigated three separate times in this project, because every time it was
asked it was answered by a judgment call. A judgment call cannot be an
acceptance criterion: it is not reproducible, it cannot be re-graded from its
own output, and two readers can disagree forever without either being wrong.
This module converts the question into a procedure with a decidable answer -
launch the server, poll the port, assert a named JSON key and a named DOM node,
capture one screenshot, stop the server, and let THE EXIT CODE decide. A queue
row of that shape cites this script as its acceptance instead of a verdict
somebody typed.

THE EXIT CODE IS THE INTERFACE, and the codes are distinct because a reader must
be able to tell a launch failure from a content failure without reading prose.
Collapsing them is the specific defect that made the question unanswerable:
"it did not work" describes a server that never bound and a server that bound
and served a broken page equally well, and those are acted on differently.

    0  PASS         every assertion this run made held.
    1  USAGE        the invocation was wrong. Remapped off argparse's own 2,
                    which would otherwise collide with PORT_BUSY.
    2  PORT_BUSY    the target port was ALREADY bound before anything launched.
                    Refused rather than measuring somebody else's listener or
                    stacking a second one behind it.
    3  LAUNCH       our server never became reachable inside the deadline, or
                    exited first. The child's own exit code is reported verbatim
                    when it has one, because it is already a distinct interface
                    (0 ok, 1 config, 2 bind, 3 certificate).
    4  TRANSPORT    reachable, but an HTTP exchange did not complete.
    5  JSON         the JSON assertion failed.
    6  DOM          the DOM assertion failed.
    7  CONTROL      a known-good control failed, so every negative this run
                    produced is INCONCLUSIVE rather than false. Outranks all of
                    the above - see the next paragraph.
    8  CLEANUP      the assertions decided, but the probe could not prove the
                    server stopped and the port came back.

A NEGATIVE MEASUREMENT WITH NO KNOWN-GOOD CONTROL IS WORTHLESS, and on this box
that is measured rather than assumed: browser-pane events here have been
observed silently faked, producing three false findings in one session. So every
instrument this module decides with is exercised in BOTH directions in the same
pass, before and against the live server:

    static, before launch   the id finder finds an id that IS in a document this
                            module carries, and does NOT find one that is not.
                            The same two arms for the JSON path reader.
    live, against the server the id finder does NOT find an id index.html
                            demonstrably has no reason to carry, and the JSON
                            path reader does NOT resolve a route template
                            ``clockspeed/surface/api/health.py`` does not
                            publish.

The first pair says an "absent" verdict is not blindness. The second says a
"present" verdict is not a rubber stamp. A control failure is its own exit code
because the honest report is "this run measured nothing", which is a different
statement from "the dashboard is broken" and must not be filed as one.

THE TLS CLIENT PINS THE DASHBOARD'S OWN CERTIFICATE AS ITS CA, AND VERIFICATION
STAYS ON. The obvious move here is ``check_hostname = False`` plus
``verify_mode = CERT_NONE``, on the grounds that the certificate is self-signed
and no public CA vouches for it. That move is available and it is the WRONG
default, for a reason this repository already measured: ``scripts/make_cert.py``
mints the pair with ``subjectAltName=DNS:localhost,IP:127.0.0.1`` precisely so
an address client can verify without lowering anything, and
``tests/surface/test_server.py`` verifies every one of its arms that way. A
probe that waived verification would be a probe that could not tell the
dashboard's certificate from any other, and "the page came back" would stop
being a statement about THIS server. So the default client trusts exactly one
file - the certificate the configuration says the server is serving - and
nothing else on this machine.

``--no-verify`` EXISTS AND IS NOT EVIDENCE ABOUT ANYTHING. It is there for a box
whose pair is somewhere the configuration does not name. A run that used it says
so on its own report, and NOTHING IN THAT RUN MAY BE CITED AS SAYING THE
CERTIFICATE IS GOOD: it was not checked, it was waived.

NO BROWSER IS EVER ASKED TO ACCEPT THAT CERTIFICATE, whichever mode is in force.
That is measured rather than assumed - no automation browser on this box will
load it - and it is why the deciding legs are an HTTP client rather than a
rendered page.

THE SCREENSHOT GOES THROUGH A PLAIN-HTTP LOOPBACK BRIDGE, because no automation
browser on this box will load that self-signed certificate - measured here more
than once. Rather than pretend otherwise, the capture leg starts a tiny
forwarder that speaks plain HTTP on loopback and re-issues each request to the
dashboard over HTTPS, and points the browser at the forwarder. THE BRIDGE TAKES
NO PORT ALLOCATION: it binds port 0 and lets the operating system choose, because
``config/ports.json`` allocates ports for services something else has to FIND,
and this one lives for one screenshot and dies. The forwarder listens on loopback
only and exists for the duration of the capture.

THE SCREENSHOT IS A PERSONAL-DATA-BEARING ARTIFACT (non-negotiables 3, 11, 12).
A dashboard rendering a real world can put a world name into a PNG, and a PNG is
not something a reader inspects before pasting. Two mechanisms, not one:

  - the child is started with save detection OFF by default, so the page has no
    world to render and the capture cannot contain one. ``--with-world`` opts in,
    and ``--help`` says what that then costs.
  - every artifact this module writes lands under the repository's GITIGNORED
    generated-artifact directory, and is reported by a repository-RELATIVE path
    so the report itself cannot spell a home directory either.

IT NEVER WRITES TO THE GAME INSTALL OR TO A SAVE DIRECTORY (non-negotiable 1).
It writes exactly three kinds of file, all under that one gitignored directory:
the child's captured output, the browser's throwaway profile, and the PNG.

CLEANUP DOES NOT RELY ON A ``finally`` ALONE, because a killed process skips its
``finally`` and the next run would then meet a bound port it did not bind. Four
mechanisms, in order of when they bite:

  1. the child is bound into a Windows job object marked kill-on-close, so the
     kernel reaps it if this process is killed outright. Best effort: a box
     that refuses the job object is reported, not silently trusted.
  2. a ``finally`` that stops the child on every path, exception included.
  3. the stop escalates - console break, then terminate, then ``taskkill /F /T``
     - each rung bounded, and the rung that worked is named in the report.
  4. the port is PROBED after the stop. A stop nothing confirmed is not a stop.

EVERY DEADLINE IS MEASURED ON A MONOTONIC CLOCK and never on wall time. An NTP
step backwards silently extends a wall-clock deadline, which turns a bounded
poll into an unbounded one at the worst possible moment.

EVERY EXTERNAL EFFECT IS INJECTED. :class:`Backends` carries the launcher, the
HTTP client, the port probe, the clock, the sleep and the capture backend, plus
the two measuring instruments the control grades. That is what lets the whole
decision procedure be tested on a machine with no game installed and nothing
listening, without spawning a process, binding a port, sleeping or shelling out.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import signal
import ssl
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from html.parser import HTMLParser
from http import client as http_client
from http import server as http_server
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, Protocol

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

# THIS FILE IS RUN AS A BARE SCRIPT, so neither its own directory nor the
# checkout root can be assumed on sys.path - `python tools/dashboard_probe.py`
# puts only tools/ there, and `python -m` only the working directory. Both go on
# explicitly, which is the idiom drift_guard.py already uses for each half.
#
# CS-910: the BARE module name `toolpath` is required. tools/ carries no
# __init__.py, so spelling it `tools.toolpath` hands mypy the same file under two
# module names and it refuses the run.
_TOOLS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TOOLS_DIR.parent
for _entry in (str(_TOOLS_DIR), str(_REPO_ROOT)):
    if _entry not in sys.path:
        sys.path.insert(0, _entry)

from toolpath import resolve_tool  # noqa: E402

from clockspeed.surface import config, server  # noqa: E402
from clockspeed.surface.api import contract, health  # noqa: E402

__all__ = [
    "EPILOG",
    "EXIT_CLEANUP",
    "EXIT_CONTROL",
    "EXIT_DOM",
    "EXIT_JSON",
    "EXIT_LAUNCH",
    "EXIT_PASS",
    "EXIT_PORT_BUSY",
    "EXIT_TRANSPORT",
    "EXIT_USAGE",
    "Backends",
    "BridgeServer",
    "Capture",
    "Exchange",
    "Finding",
    "Options",
    "Report",
    "ServerHandle",
    "client_context",
    "decide",
    "document_ids",
    "exit_reading",
    "follow_path",
    "https_client",
    "main",
    "parse_args",
    "probe",
    "render",
    "value_shape",
]


# ---------------------------------------------------------------------------
# Exit codes. THE INTERFACE. Documented in the module docstring above and in
# docs/OPERATIONS.md; distinct so a runbook can branch on one.
# ---------------------------------------------------------------------------

EXIT_PASS: Final = 0
EXIT_USAGE: Final = 1
EXIT_PORT_BUSY: Final = 2
EXIT_LAUNCH: Final = 3
EXIT_TRANSPORT: Final = 4
EXIT_JSON: Final = 5
EXIT_DOM: Final = 6
EXIT_CONTROL: Final = 7
EXIT_CLEANUP: Final = 8

#: Stage name to exit code, in the order the stages run. The FIRST failing stage
#: in this order names the exit code, with one exception stated below it: a
#: control failure outranks everything, because it says the run measured nothing.
STAGE_CODES: Final = (
    ("port", EXIT_PORT_BUSY),
    ("launch", EXIT_LAUNCH),
    ("transport", EXIT_TRANSPORT),
    ("json", EXIT_JSON),
    ("dom", EXIT_DOM),
    ("cleanup", EXIT_CLEANUP),
)

#: The stage whose failure invalidates the measurement rather than condemning
#: the subject. Held apart from :data:`STAGE_CODES` because it does not take its
#: turn in that order - it pre-empts it.
STAGE_CONTROL: Final = "control"

#: The stage a screenshot finding is filed under. It NEVER decides the exit
#: code: capture depends on a browser being installed, and a gate that goes red
#: because a box has no Chrome is a gate that gets disabled and then enforces
#: nothing. The screenshot is EVIDENCE. The JSON and DOM legs are the VERDICT.
STAGE_EVIDENCE: Final = "screenshot"

#: Verdict vocabulary, closed. ``skip`` is for a stage that never ran because an
#: earlier one made it meaningless; ``unavailable`` is for a stage whose backend
#: is absent from this box, which is not a finding about the dashboard.
PASS: Final = "pass"  # noqa: S105 - a verdict word, not a credential
FAIL: Final = "fail"
SKIP: Final = "skip"
UNAVAILABLE: Final = "unavailable"


# ---------------------------------------------------------------------------
# What is asserted. Every expected value is READ FROM ITS OWNER rather than
# spelled here, so a rename below moves one literal and this file moves none.
# ---------------------------------------------------------------------------

#: The endpoint the JSON leg asks. Health is the right one and the only right
#: one: ``clockspeed/surface/api/health.py`` guarantees it answers 200 and
#: nothing else, so a non-200 from it is unambiguously the server and never the
#: question. It also names no path, so its body is safe to report.
HEALTH_PATH: Final = health.ENDPOINT

#: The document the DOM leg asks for, read from the server's own static table so
#: the two cannot disagree about which request path serves the page.
DOCUMENT_PATH: Final = next(
    request for request, (name, _type) in server.STATIC_ROUTES.items() if name == "index.html"
)

#: The JSON keys asserted, as key paths into the parsed body, each with the
#: value it must equal. ``data.endpoints[/api/health]`` is the load-bearing one:
#: a static string can come back from a stub, but that key is only ``live`` when
#: the route table was actually assembled and bound.
JSON_ASSERTIONS: Final = (
    (("status",), contract.STATUS_OK),
    (("endpoint",), health.ENDPOINT),
    (("data", "endpoints", health.ENDPOINT), health.LIVE),
)

#: A key path whose LAST segment is a route template section 7.1 does not
#: publish. The live JSON control asserts this does NOT resolve. If it ever does,
#: the reader is resolving something other than what it was asked for.
JSON_CONTROL_ABSENT: Final = ("data", "endpoints", "/api/<probe-control-never-published>")

#: A key path that must resolve in any health body, used as the live positive
#: control arm's partner. Reported by SHAPE, never by value.
JSON_CONTROL_PRESENT: Final = ("data", "app_version")

#: Every element ``clockspeed/surface/web/app.js`` reaches for by id. NOT an
#: arbitrary sample: these are exactly the nodes whose absence provably breaks
#: the page, because the script asks for each one by name and writes into it.
#: They are LITERALS here on purpose - a probe that read the ids out of the
#: document it is grading would assert nothing at all.
REQUIRED_NODE_IDS: Final = (
    "pin",
    "probe-note",
    "endpoint-rows",
    "world-note",
    "world-facts",
    "count-scroller",
    "count-table",
    "count-rows",
    "unmodeled-note",
    "unmodeled-list",
    "refresh",
)

#: An id the dashboard has no reason to carry. The live DOM control asserts it
#: is NOT found, which is what makes every "found" above mean something.
DOM_CONTROL_ABSENT: Final = "clockspeed-probe-control-never-present"

#: The document the static control grades the id finder against, and the id in
#: it. Deliberately awkward - an unquoted attribute, a self-closing tag and a
#: nested element - so a finder that only works on tidy markup fails here rather
#: than against the real page.
CONTROL_DOCUMENT: Final = (
    "<!doctype html><html><head><title>control</title></head><body>"
    "<div class=outer><br/><span id='clockspeed-probe-control-present'>x</span></div>"
    "</body></html>"
)
DOM_CONTROL_PRESENT: Final = "clockspeed-probe-control-present"

#: The payload the static control grades the key-path reader against, and the
#: value at its leaf. The leaf VALUE is checked as well as its presence, so a
#: reader that reports every path found while returning nothing useful is caught
#: by the same arm.
CONTROL_LEAF: Final = "value"
CONTROL_PAYLOAD: Final = {"status": "ok", "data": {"nested": {"leaf": CONTROL_LEAF}}}
JSON_STATIC_PRESENT: Final = ("data", "nested", "leaf")
JSON_STATIC_ABSENT: Final = ("data", "nested", "no-such-leaf")


# ---------------------------------------------------------------------------
# Defaults. Bounded everywhere; nothing here waits forever.
# ---------------------------------------------------------------------------

#: How long the server has to become reachable. Generous: the child imports the
#: whole package and mints a TLS context before it binds.
LAUNCH_DEADLINE_S: Final = 30.0

#: How long one HTTP exchange has.
REQUEST_DEADLINE_S: Final = 10.0

#: How long each rung of the stop escalation has before the next rung fires.
STOP_RUNG_S: Final = 5.0

#: How long the port has to come back free after the child is gone. A listener
#: in TIME_WAIT does not hold an accepting socket, so this is short.
PORT_FREE_DEADLINE_S: Final = 10.0

#: How long the browser has to render and write a PNG.
CAPTURE_DEADLINE_S: Final = 60.0

#: Gap between polls. Small enough that a fast start is not padded, large enough
#: that the poll is not a spin.
POLL_INTERVAL_S: Final = 0.25

#: How long the launcher waits to see whether the child dies on the spot. Short:
#: it is an early-death detector, not a readiness wait - readiness is the poll.
SETTLE_S: Final = 0.5

#: The forcible-kill tool. A NAME, resolved at runtime through
#: ``tools/toolpath.py`` and never spelled as a path - non-negotiable 3, and
#: CS-910 for why a bare name handed to a spawn is itself the defect.
TASKKILL_NAME: Final = "taskkill"

#: The Windows job-object constants used by :func:`_adopt`.
#: ``JobObjectExtendedLimitInformation`` is information class 9;
#: ``JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`` is 0x2000, and it sits in the
#: ``LimitFlags`` field of the basic-limit struct the extended one starts with.
#: THE STRUCT IS WRITTEN AS A RAW BUFFER rather than mirrored as a
#: ``ctypes.Structure``: a mirrored layout would be a second copy of an ABI this
#: module has no business owning, and only one field is being set.
JOB_EXTENDED_LIMIT_CLASS: Final = 9
JOB_KILL_ON_CLOSE: Final = 0x2000
JOB_LIMIT_STRUCT_BYTES: Final = 144
JOB_LIMIT_FLAGS_OFFSET: Final = 16

#: Live job-object handles. HELD FOR THE PROCESS LIFETIME ON PURPOSE: the kernel
#: reaps a kill-on-close job when the LAST handle to it closes, so letting one be
#: garbage collected would undo the very mechanism it exists to provide.
_JOBS: Final[list[int]] = []

#: Where every artifact this module writes lands, relative to the repository
#: root. ``/data/`` is anchored in ``.gitignore`` as the generated-artifact
#: directory, so nothing written here can reach a commit.
ARTIFACT_PARTS: Final = ("data", "dashboard_probe")

#: The capture filename. Fixed, so a run overwrites the last one rather than
#: accumulating PNGs of the operator's dashboard on disk.
CAPTURE_NAME: Final = "dashboard.png"

#: Where the child's own output is captured. Its refusal lines are fixed text
#: plus a port integer plus a class name (``clockspeed/surface/server.py``
#: states why that is safe), which is what makes echoing this file safe.
CHILD_OUTPUT_NAME: Final = "server-output.txt"

#: The browser's throwaway profile. Isolated so the capture never opens, reads
#: or writes the operator's own browser profile.
BROWSER_PROFILE_NAME: Final = "browser-profile"

#: Browser executables tried in order, resolved from PATH and then from the
#: program-files location the ENVIRONMENT names. No absolute path is spelled
#: here: an absolute path in a tracked file is forbidden outright, and a browser
#: is exactly the kind of thing that lives somewhere else on the next box.
BROWSER_NAMES: Final = ("chrome", "msedge", "chromium")
BROWSER_SUFFIXES: Final = (
    ("Google", "Chrome", "Application", "chrome.exe"),
    ("Microsoft", "Edge", "Application", "msedge.exe"),
)
PROGRAM_FILES_ENV: Final = ("PROGRAMFILES", "PROGRAMFILES(X86)")

#: The viewport the capture renders at. Wide enough that the endpoint table is
#: not the only thing on the page.
CAPTURE_WIDTH: Final = 1280
CAPTURE_HEIGHT: Final = 900

#: Milliseconds of VIRTUAL time the browser is allowed to burn before it
#: screenshots. MEASURED, and the reason the flag is here at all: without it the
#: first real capture of this gate rendered the page's empty states - every
#: panel reading "reading ..." - because Chrome shoots on load and this page
#: fills itself from fetches that land after load. A picture of a page that has
#: not fetched anything is a picture that would look identical against a server
#: answering nothing, which makes it evidence of nothing. Virtual time rather
#: than a wall-clock sleep, so a fast box is not padded and a slow one is not cut
#: off.
CAPTURE_SETTLE_MS: Final = 5000


# ---------------------------------------------------------------------------
# The instruments. Pure, and graded by the control before anything is launched.
# ---------------------------------------------------------------------------


class _IdCollector(HTMLParser):
    """Collect every ``id`` attribute a document declares.

    A REAL PARSE AND NOT A REGULAR EXPRESSION. A regex over markup matches
    ``id=`` inside a comment and inside an attribute value, and this repository's
    ``index.html`` is more comment than element - a substring search over a file
    that documents itself is a search of the documentation.
    """

    def __init__(self) -> None:
        """Start with nothing collected."""
        super().__init__()
        self.found: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Record the id this tag declares, if it declares one.

        Args:
            tag: The element name, unused - an id is an id on any element.
            attrs: The attributes, as the parser decoded them.
        """
        del tag
        for name, value in attrs:
            if name == "id" and value:
                self.found.add(value)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Record the id a self-closing tag declares.

        The base class routes ``<br/>`` here and NOT to
        :meth:`handle_starttag`, so a finder that overrode only the first would
        be blind to every self-closing element. The control document carries one
        for exactly that reason.

        Args:
            tag: The element name.
            attrs: The attributes.
        """
        self.handle_starttag(tag, attrs)


def document_ids(document: str) -> frozenset[str]:
    """Every element id a document declares.

    Args:
        document: The markup, decoded.

    Returns:
        The ids. Empty for markup that declares none, and for markup that is
        not markup at all - which is why the control grades this rather than
        trusting it.
    """
    collector = _IdCollector()
    collector.feed(document)
    collector.close()
    return frozenset(collector.found)


def follow_path(payload: object, path: tuple[str, ...]) -> tuple[bool, object]:
    """Follow a key path into a parsed JSON payload.

    NAMED APART FROM THE FIELD IT IS THE DEFAULT FOR. :class:`Backends` carries
    a ``read_path`` seam whose default is this function; giving the two the same
    spelling would make the class body read its own not-yet-bound name.

    A KEY PATH RATHER THAN AN RFC 6901 POINTER, because every key this module
    asks for is a route template and route templates contain slashes. Escaping
    them would put a second spelling of ``/api/health`` in this file, and a fact
    spelled twice is a fact that drifts.

    Args:
        payload: The parsed body, or any part of it.
        path: The keys to follow, outermost first.

    Returns:
        ``(True, value)`` when every key resolved, ``(False, None)`` otherwise.
        A non-mapping encountered part way down is a miss, not an error: this is
        an instrument and an instrument that raises cannot report a negative.
    """
    cursor = payload
    for key in path:
        if not isinstance(cursor, dict) or key not in cursor:
            return (False, None)
        cursor = cursor[key]
    return (True, cursor)


#: Windows termination statuses this gate can actually produce, rendered rather
#: than left as ten opaque digits. MEASURED: the console-break rung produced
#: 3221225786 on the first real run, and a report that prints that number and
#: nothing else cannot be re-graded - it is indistinguishable from a crash by
#: anyone who does not already know the constant. THE BREAK RUNG REALLY DOES
#: TERMINATE rather than unwind: CTRL_BREAK_EVENT raises SIGBREAK, not SIGINT,
#: so the server's own SIGINT shutdown never runs. That is an acceptable outcome
#: - the listener is released and the port probe below confirms it - but the
#: report has to say so rather than imply a graceful stop.
EXIT_READINGS: Final[Mapping[int, str]] = MappingProxyType(
    {
        0xC000013A: "STATUS_CONTROL_C_EXIT - the console break terminated it",
        0xC0000005: "STATUS_ACCESS_VIOLATION",
        0xC000041D: "STATUS_FATAL_USER_CALLBACK_EXCEPTION",
        1: "the process was terminated",
    }
)


def exit_reading(code: int) -> str:
    """Render a child's exit code so a reader can act on it.

    Args:
        code: What the process reported.

    Returns:
        The number, plus what it means where this module knows.
    """
    known = EXIT_READINGS.get(code)
    return f"{code} ({known})" if known else str(code)


def value_shape(value: object) -> str:
    """Render a value's SHAPE, never its content.

    THIS IS A REDACTION BOUNDARY AND NOT A FORMATTING CHOICE. A failing
    assertion is exactly where an unexpected value turns up, and an unexpected
    value in a body this probe did not write could be anything. Rendering the
    type and the size says enough to diagnose and cannot leak (non-negotiable
    12). Where a value MATCHED a constant this module owns, the caller prints
    that constant instead - it is already public, in this file.

    Args:
        value: Whatever was found.

    Returns:
        A short description carrying no string content.
    """
    if isinstance(value, bool):
        return f"bool {value}"
    if isinstance(value, int):
        return f"int {value}"
    if isinstance(value, str):
        return f"string of {len(value)} characters"
    if isinstance(value, list):
        return f"array of {len(value)} entries"
    if isinstance(value, dict):
        return f"object with {len(value)} keys"
    return "null" if value is None else type(value).__name__


# ---------------------------------------------------------------------------
# Values that cross this module's boundary.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Exchange:
    """What came back from one HTTP request, or why nothing did.

    Attributes:
        status: The HTTP status, or None when the exchange did not complete.
        body: The decoded body, empty when there was none.
        content_type: The declared content type, empty when there was none.
        error: A CLASS NAME and errno, never a message. ``OSError.__str__``
            appends a filename when the interpreter set one, and that filename
            can be a path on this machine (non-negotiable 12), so the summary
            comes from ``clockspeed/surface/server.py``'s own ``cause_summary``
            rather than from ``str(exc)``. Empty when the exchange completed.
    """

    status: int | None
    body: str
    content_type: str
    error: str


@dataclass(frozen=True)
class Capture:
    """The outcome of the screenshot leg.

    Attributes:
        taken: True when a PNG was written.
        where: A REPOSITORY-RELATIVE path, or empty. Never absolute: an absolute
            path here could spell a home directory into the report.
        reason: Why not, when ``taken`` is False. Empty otherwise.
    """

    taken: bool
    where: str
    reason: str


@dataclass(frozen=True)
class Finding:
    """One thing the probe asserted, and what it observed.

    A gate that prints only PASS or FAIL cannot be re-graded from its own
    output, so every assertion becomes one of these and the whole list is
    rendered whatever the verdict.

    Attributes:
        stage: Which stage owns it - a member of :data:`STAGE_CODES`'s names,
            :data:`STAGE_CONTROL` or :data:`STAGE_EVIDENCE`.
        name: What was asserted, spelled the way it was asserted.
        verdict: :data:`PASS`, :data:`FAIL`, :data:`SKIP` or
            :data:`UNAVAILABLE`.
        detail: What was observed, verbatim. Values are rendered through
            :func:`value_shape` unless they matched a constant this module owns,
            in which case the constant is already public and is printed whole.
    """

    stage: str
    name: str
    verdict: str
    detail: str


@dataclass(frozen=True)
class Report:
    """Everything one run asserted, and the code it decided.

    Attributes:
        code: The process exit code.
        findings: Every assertion, in the order it was made.
    """

    code: int
    findings: tuple[Finding, ...]


@dataclass(frozen=True)
class Options:
    """What the operator asked for.

    Attributes:
        port: The port to launch the dashboard on and poll.
        node_ids: The element ids the served document must carry.
        with_world: True to let the child detect a save. Off by default,
            because a rendered world puts a world name in the screenshot.
        verify: True to verify TLS against the dashboard's own pinned
            certificate. False WAIVES verification, and a waived run is not
            evidence about the certificate.
        screenshot: True to attempt a capture.
        artifact_dir: Where artifacts land. Absolute at runtime, reported
            relative.
        launch_deadline_s: How long the server has to answer.
        request_deadline_s: How long one exchange has.
        stop_deadline_s: How long each stop rung has.
        poll_interval_s: The gap between polls.
    """

    port: int
    node_ids: tuple[str, ...] = REQUIRED_NODE_IDS
    with_world: bool = False
    verify: bool = True
    screenshot: bool = True
    artifact_dir: Path = field(default_factory=Path)
    launch_deadline_s: float = LAUNCH_DEADLINE_S
    request_deadline_s: float = REQUEST_DEADLINE_S
    stop_deadline_s: float = STOP_RUNG_S
    poll_interval_s: float = POLL_INTERVAL_S


class ServerHandle(Protocol):
    """What the probe needs from the process it started.

    A PROTOCOL AND NOT A CLASS, because the whole decision procedure has to be
    gradeable without starting a process. The real implementation is
    :class:`_ChildServer`; a test supplies its own.
    """

    def exit_code(self) -> int | None:
        """The child's exit code, or None while it is still running.

        Returns:
            The code, or None.
        """
        ...

    def stop(self) -> str:
        """Stop the child, bounded, and say how.

        Returns:
            A one-line verbatim account naming the rung that worked, so a
            report can be re-graded without rerunning anything.
        """
        ...


@dataclass(frozen=True)
class Backends:
    """Every external effect, injected.

    THE TWO INSTRUMENTS ARE HERE TOO, and that is the point rather than an
    over-generalisation: :attr:`find_ids` and :attr:`read_path` are what the
    verdict is measured WITH, so a control that cannot substitute a broken one
    is a control that never proves the instrument works.

    Attributes:
        launch: Start the dashboard on a port and return a handle.
        fetch: Issue one request and return what came back.
        port_bound: True when something is accepting on that port.
        clock: A MONOTONIC clock. Never wall time - an NTP step backwards
            silently extends a wall-clock deadline.
        sleep: Wait between polls.
        capture: Take a screenshot of the dashboard, or None when this box has
            no browser automation at all.
        find_ids: Every element id in a document.
        read_path: Follow a key path into a parsed payload, returning whether
            it resolved and what it resolved to.
    """

    launch: Callable[[int], ServerHandle]
    fetch: Callable[[int, str, float], Exchange]
    port_bound: Callable[[int], bool]
    clock: Callable[[], float]
    sleep: Callable[[float], None]
    capture: Callable[[int], Capture] | None
    find_ids: Callable[[str], frozenset[str]] = document_ids
    read_path: Callable[[object, tuple[str, ...]], tuple[bool, object]] = follow_path


# ---------------------------------------------------------------------------
# The stages.
# ---------------------------------------------------------------------------


def control_stage(backends: Backends) -> tuple[Finding, ...]:
    """Grade both instruments in both directions, before anything is launched.

    THIS IS THE STAGE THE WHOLE MODULE IS BUILT AROUND. Everything below it
    reports "found" or "absent", and neither word means anything until the thing
    doing the finding has been shown to do both. Four arms, because two
    instruments times two directions is four:

      - a finder that returns nothing calls every node absent, and the naive
        report of that is "the dashboard's page is broken". MEASURED on the
        first build of this module: it returned the DOM code, blaming the
        subject for a fault in the instrument.
      - a finder that returns everything calls every node present, and its
        report is a green run that asserted nothing.

    The same pair for the key-path reader. A failure here is
    :data:`EXIT_CONTROL`, which says the run measured nothing - a different
    claim from "the dashboard is broken", and it must never be filed as one.

    Args:
        backends: The injected effects, for the two instruments.

    Returns:
        Four findings.
    """
    seen = backends.find_ids(CONTROL_DOCUMENT)
    hit, value = backends.read_path(CONTROL_PAYLOAD, JSON_STATIC_PRESENT)
    miss, _absent = backends.read_path(CONTROL_PAYLOAD, JSON_STATIC_ABSENT)
    return (
        _arm(
            "the id finder sees an id that IS present",
            found=DOM_CONTROL_PRESENT in seen,
            want=True,
            detail=f"it declared {len(seen)} id(s) in the control document",
        ),
        _arm(
            "the id finder does NOT see an id that is absent",
            found=DOM_CONTROL_ABSENT in seen,
            want=False,
            detail="a finder that finds everything grades nothing",
        ),
        _arm(
            "the key reader resolves a path that IS present",
            found=hit and value == CONTROL_LEAF,
            want=True,
            detail="it followed the control payload to its leaf",
        ),
        _arm(
            "the key reader does NOT resolve a path that is absent",
            found=miss,
            want=False,
            detail="a reader that resolves everything grades nothing",
        ),
    )


def _arm(name: str, *, found: bool, want: bool, detail: str) -> Finding:
    """One control arm.

    Args:
        name: What the arm asserts.
        found: What the instrument said.
        want: What a working instrument would say.
        detail: What to report when it held.

    Returns:
        The finding, always on :data:`STAGE_CONTROL`.
    """
    return Finding(
        stage=STAGE_CONTROL,
        name=name,
        verdict=PASS if found == want else FAIL,
        detail=detail if found == want else "IT DID NOT; every verdict this run made is void",
    )


def port_stage(options: Options, backends: Backends) -> tuple[Finding, ...]:
    """Refuse to launch behind a listener that is already there.

    Args:
        options: What the operator asked for.
        backends: The injected effects.

    Returns:
        One finding. Failing means nothing was launched.
    """
    bound = backends.port_bound(options.port)
    if bound:
        return (
            Finding(
                stage="port",
                name=f"the port {options.port} is free before launch",
                verdict=FAIL,
                detail=(
                    "something is already accepting on it. Refusing to launch a second "
                    "server behind it - a probe that measured somebody else's listener "
                    "would report on a process it did not start and cannot stop."
                ),
            ),
        )
    return (
        Finding(
            stage="port",
            name=f"the port {options.port} is free before launch",
            verdict=PASS,
            detail="nothing was accepting on it",
        ),
    )


def launch_stage(
    options: Options,
    backends: Backends,
    handle: ServerHandle,
) -> tuple[Finding, ...]:
    """Poll until the server answers, it exits, or the deadline passes.

    LIVENESS IS THE ANSWER AND NOT THE PROCESS. A pid that exists is not a
    server that serves: the child binds, wraps the socket in TLS and only then
    accepts, and every one of those can fail after the process is up. So the
    poll asks the health endpoint and accepts nothing less than a completed
    exchange.

    Args:
        options: What the operator asked for.
        backends: The injected effects.
        handle: The child, already started.

    Returns:
        One finding. Failing means no assertion below it can mean anything.
    """
    name = f"the server answers {HEALTH_PATH} within {options.launch_deadline_s:g}s"
    deadline = backends.clock() + options.launch_deadline_s
    attempts = 0
    last = ""
    while backends.clock() < deadline:
        attempts += 1
        code = handle.exit_code()
        if code is not None:
            return (
                Finding(
                    stage="launch",
                    name=name,
                    verdict=FAIL,
                    detail=(
                        f"the child exited {code} after {attempts} attempt(s) before it "
                        f"ever answered. That code is the server's own interface: "
                        f"{server.EXIT_OK} clean, 1 configuration, "
                        f"{server.EXIT_BIND_FAILED} bind, "
                        f"{server.EXIT_CERTIFICATE} certificate."
                    ),
                ),
            )
        exchange = backends.fetch(options.port, HEALTH_PATH, options.request_deadline_s)
        if not exchange.error:
            return (
                Finding(
                    stage="launch",
                    name=name,
                    verdict=PASS,
                    detail=f"answered on attempt {attempts} with HTTP {exchange.status}",
                ),
            )
        last = exchange.error
        backends.sleep(options.poll_interval_s)
    return (
        Finding(
            stage="launch",
            name=name,
            verdict=FAIL,
            detail=(
                f"never answered across {attempts} attempt(s); the last exchange failed "
                f"with {last or 'no attempt inside the deadline'}"
            ),
        ),
    )


def json_stage(options: Options, backends: Backends) -> tuple[Finding, ...]:
    """Assert the named JSON keys against a live health body.

    Args:
        options: What the operator asked for.
        backends: The injected effects.

    Returns:
        One finding for the exchange, then one per asserted key.
    """
    exchange = backends.fetch(options.port, HEALTH_PATH, options.request_deadline_s)
    findings = [_exchange_finding(HEALTH_PATH, exchange, server.CONTENT_TYPE_JSON)]
    if exchange.error or exchange.status != contract.HTTP_OK:
        return (*findings, _skipped("json", "the asserted keys", "the exchange did not stand"))

    try:
        payload = json.loads(exchange.body)
    except json.JSONDecodeError:
        # THE EXCEPTION IS NOT RENDERED. `JSONDecodeError.__str__` embeds a
        # slice of the document it failed on, and the document is a body this
        # process did not author.
        return (
            *findings,
            Finding(
                stage="json",
                name="the body parses as JSON",
                verdict=FAIL,
                detail=f"it did not; {len(exchange.body)} characters were returned",
            ),
        )
    findings.append(
        Finding(
            stage="json",
            name="the body parses as JSON",
            verdict=PASS,
            detail=value_shape(payload),
        )
    )
    # THE LIVE CONTROL, in the same pass and against the same body. The static
    # arms proved the reader can miss; this one proves it misses THIS payload,
    # so every "found" below is a statement about the body rather than about a
    # reader that resolves whatever it is handed.
    resolved, _value = backends.read_path(payload, JSON_CONTROL_ABSENT)
    findings.append(
        _arm(
            f"the reader does NOT resolve {_spell(JSON_CONTROL_ABSENT)} in the live body",
            found=resolved,
            want=False,
            detail="a template section 7.1 does not publish, and the body does not carry",
        )
    )
    findings.extend(_key_findings(backends, payload))
    return tuple(findings)


def _key_findings(backends: Backends, payload: object) -> list[Finding]:
    """Grade every asserted key path against one parsed payload.

    Args:
        backends: The injected effects, for the key-path reader.
        payload: The parsed body.

    Returns:
        One finding per assertion.
    """
    findings: list[Finding] = []
    for path, expected in JSON_ASSERTIONS:
        spelled = _spell(path)
        found, value = backends.read_path(payload, path)
        if not found:
            findings.append(
                Finding(stage="json", name=spelled, verdict=FAIL, detail="the key is absent")
            )
        elif value == expected:
            findings.append(
                Finding(stage="json", name=spelled, verdict=PASS, detail=f'found "{expected}"')
            )
        else:
            findings.append(
                Finding(
                    stage="json",
                    name=spelled,
                    verdict=FAIL,
                    detail=f'expected "{expected}"; found {value_shape(value)}',
                )
            )
    return findings


def dom_stage(options: Options, backends: Backends) -> tuple[Finding, ...]:
    """Assert the named DOM nodes against the live document.

    WHAT THIS PROVES AND WHAT IT DOES NOT, stated so nobody upgrades it later.
    It proves the document was SERVED and carries every node the page script
    reaches for. It does NOT prove the script ran - the served markup holds the
    empty states rather than any value. The screenshot leg is what would show
    the page filled in, and that leg cannot decide because it needs a browser.

    Args:
        options: What the operator asked for.
        backends: The injected effects.

    Returns:
        One finding for the exchange, then one per required node.
    """
    exchange = backends.fetch(options.port, DOCUMENT_PATH, options.request_deadline_s)
    html_type = server.STATIC_ROUTES[DOCUMENT_PATH][1]
    findings = [_exchange_finding(DOCUMENT_PATH, exchange, html_type)]
    if exchange.error or exchange.status != contract.HTTP_OK:
        return (*findings, _skipped("dom", "the required nodes", "the exchange did not stand"))

    present = backends.find_ids(exchange.body)
    # THE LIVE CONTROL, against the same document every node below is graded in.
    findings.append(
        _arm(
            f'the finder does NOT declare id="{DOM_CONTROL_ABSENT}" in the live document',
            found=DOM_CONTROL_ABSENT in present,
            want=False,
            detail="an id the dashboard has no reason to carry, and does not",
        )
    )
    findings.extend(
        Finding(
            stage="dom",
            name=f'the document declares id="{node}"',
            verdict=PASS if node in present else FAIL,
            detail=(
                f"matched among {len(present)} declared id(s)"
                if node in present
                else f"absent; {len(present)} other id(s) were declared"
            ),
        )
        for node in options.node_ids
    )
    return tuple(findings)


def evidence_stage(options: Options, backends: Backends) -> tuple[Finding, ...]:
    """Capture one screenshot, and DEGRADE rather than fail without a browser.

    Args:
        options: What the operator asked for.
        backends: The injected effects.

    Returns:
        One finding, never with a verdict that decides the exit code.
    """
    name = "a screenshot of the rendered page"
    if not options.screenshot:
        return (Finding(stage=STAGE_EVIDENCE, name=name, verdict=SKIP, detail="not requested"),)
    if backends.capture is None:
        return (
            Finding(
                stage=STAGE_EVIDENCE,
                name=name,
                verdict=UNAVAILABLE,
                detail="no browser automation backend on this box",
            ),
        )
    taken = backends.capture(options.port)
    if not taken.taken:
        return (
            Finding(
                stage=STAGE_EVIDENCE,
                name=name,
                verdict=UNAVAILABLE,
                detail=taken.reason,
            ),
        )
    return (
        Finding(
            stage=STAGE_EVIDENCE,
            name=name,
            verdict=PASS,
            detail=(
                f"written to {taken.where} - a PERSONAL-DATA-BEARING ARTIFACT, "
                f"under the gitignored generated-artifact directory"
            ),
        ),
    )


def cleanup_stage(
    options: Options,
    backends: Backends,
    handle: ServerHandle | None,
) -> tuple[Finding, ...]:
    """Stop the child and PROVE the port came back.

    A STOP NOTHING CONFIRMED IS NOT A STOP. ``terminate`` returns before the
    process is gone and a wrapper can outlive the thing it wrapped, so the
    verdict here is the port probe rather than the call's return.

    Args:
        options: What the operator asked for.
        backends: The injected effects.
        handle: The child, or None when nothing was launched.

    Returns:
        One finding for the stop, and one for the port.
    """
    if handle is None:
        return (
            Finding(
                stage="cleanup",
                name="the server is stopped",
                verdict=SKIP,
                detail="nothing was launched",
            ),
        )
    how = handle.stop()
    # THE STOP'S OWN ACCOUNT IS NOT THE VERDICT. A handle can escalate through
    # every rung and still be looking at a live process, so the question asked
    # here is the structural one - does the child have an exit code now - rather
    # than anything parsed out of prose.
    settled = handle.exit_code()
    findings = [
        Finding(
            stage="cleanup",
            name="the server is stopped",
            verdict=PASS if settled is not None else FAIL,
            detail=how
            if settled is not None
            else f"{how}. IT IS STILL RUNNING: the child has no exit code",
        ),
        _port_freed(options, backends),
    ]
    return tuple(findings)


def _port_freed(options: Options, backends: Backends) -> Finding:
    """Poll until the port comes back, or report that it did not.

    THE SECOND HALF OF "IT CLEANS UP AFTER ITSELF", and the half that catches
    what the first cannot: a wrapper can exit while the listener it started is
    still held by something further down its tree. A port that never comes back
    meets the NEXT run as :data:`EXIT_PORT_BUSY`, so it is named here, once,
    while the run that caused it is still on screen.

    Args:
        options: What the operator asked for.
        backends: The injected effects.

    Returns:
        The finding.
    """
    name = f"the port {options.port} is free again"
    deadline = backends.clock() + PORT_FREE_DEADLINE_S
    while backends.clock() < deadline:
        if not backends.port_bound(options.port):
            return Finding(
                stage="cleanup", name=name, verdict=PASS, detail="nothing is accepting on it"
            )
        backends.sleep(options.poll_interval_s)
    return Finding(
        stage="cleanup",
        name=name,
        verdict=FAIL,
        detail=(
            f"something is STILL accepting on it {PORT_FREE_DEADLINE_S:g}s after the stop. "
            f"The next run will refuse with PORT_BUSY until it is cleared."
        ),
    )


def _exchange_finding(path: str, exchange: Exchange, expected_type: str) -> Finding:
    """Grade one HTTP exchange - it completed, and it answered 200.

    Args:
        path: The request path, a literal this repository authored.
        exchange: What came back.
        expected_type: The content type the server's own table declares.

    Returns:
        The finding. Its stage is ``transport`` when nothing came back at all
        and the owning content stage otherwise, so a dead socket is never filed
        as a content defect.
    """
    if exchange.error:
        return Finding(
            stage="transport",
            name=f"GET {path} completes",
            verdict=FAIL,
            detail=f"the exchange failed with {exchange.error}",
        )
    stage = "json" if path == HEALTH_PATH else "dom"
    if exchange.status != contract.HTTP_OK:
        return Finding(
            stage=stage,
            name=f"GET {path} answers HTTP {contract.HTTP_OK}",
            verdict=FAIL,
            detail=f"it answered HTTP {exchange.status}",
        )
    kind = exchange.content_type.split(";", maxsplit=1)[0].strip()
    wanted = expected_type.split(";", maxsplit=1)[0].strip()
    if kind != wanted:
        return Finding(
            stage=stage,
            name=f"GET {path} answers HTTP {contract.HTTP_OK}",
            verdict=FAIL,
            detail=f'answered {contract.HTTP_OK} but declared "{kind}", not "{wanted}"',
        )
    return Finding(
        stage=stage,
        name=f"GET {path} answers HTTP {contract.HTTP_OK}",
        verdict=PASS,
        detail=f'HTTP {exchange.status}, "{kind}", {len(exchange.body)} characters',
    )


def _skipped(stage: str, name: str, why: str) -> Finding:
    """A stage that never ran because an earlier one made it meaningless.

    Args:
        stage: The owning stage.
        name: What would have been asserted.
        why: Why it was not.

    Returns:
        The finding.
    """
    return Finding(stage=stage, name=name, verdict=SKIP, detail=why)


def _spell(path: tuple[str, ...]) -> str:
    """Render a key path the way a reader would type it.

    Args:
        path: The keys, outermost first.

    Returns:
        Something like ``data.endpoints["/api/health"]``.
    """
    rendered = path[0]
    for key in path[1:]:
        rendered += f'["{key}"]' if "/" in key else f".{key}"
    return rendered


# ---------------------------------------------------------------------------
# The decision.
# ---------------------------------------------------------------------------


def decide(findings: Sequence[Finding]) -> int:
    """Turn a finding list into the one exit code.

    THE RULE, STATED ONCE. A control failure wins outright, because it says the
    run measured nothing and that is a different claim from "the dashboard is
    broken". Otherwise the EARLIEST failing stage in :data:`STAGE_CODES` order
    names the code: a launch failure explains every content failure below it, so
    reporting the content failure would name a symptom as the cause. The
    screenshot stage never decides.

    Args:
        findings: Every assertion the run made.

    Returns:
        The exit code.
    """
    failed = {finding.stage for finding in findings if finding.verdict == FAIL}
    if STAGE_CONTROL in failed:
        return EXIT_CONTROL
    for stage, code in STAGE_CODES:
        if stage in failed:
            return code
    return EXIT_PASS


def _tls_mode(options: Options) -> Finding:
    """State which TLS mode this run used, on the run's own face.

    FILED UNDER THE CONTROL STAGE, because it is a statement about the
    INSTRUMENT and not about the subject. A waived run is a run whose transport
    findings say less, and a reader must not have to reconstruct which mode was
    in force from the absence of a flag.

    Args:
        options: What the operator asked for.

    Returns:
        The finding. Never :data:`FAIL` - it reports, it does not judge.
    """
    if options.verify:
        return Finding(
            stage=STAGE_CONTROL,
            name="TLS verification",
            verdict=PASS,
            detail=(
                "pinned to the dashboard's own certificate as the trusted CA, with "
                "hostname checking left on; the pair carries an IP:127.0.0.1 SAN"
            ),
        )
    return Finding(
        stage=STAGE_CONTROL,
        name="TLS verification",
        verdict=UNAVAILABLE,
        detail=(
            "WAIVED by --no-verify. Nothing in this run is evidence about the "
            "certificate: it was not checked."
        ),
    )


def probe(options: Options, backends: Backends) -> Report:
    """Run every stage in order and decide.

    THE CHILD IS STOPPED ON EVERY PATH, exception included. That is what the
    ``finally`` is for; it is the second of the four mechanisms the module
    docstring lists, not the only one, because a process that is killed rather
    than unwound never reaches it.

    Args:
        options: What the operator asked for.
        backends: The injected effects.

    Returns:
        The report.

    Raises:
        BaseException: Whatever a backend raised, after the child is stopped.
            Re-raised rather than swallowed: an unexpected failure inside the
            gate is not a verdict about the dashboard and must not render as
            one.
    """
    findings: list[Finding] = [_tls_mode(options)]
    findings.extend(control_stage(backends))
    findings.extend(port_stage(options, backends))
    verdict = decide(findings)
    if verdict != EXIT_PASS:
        # NOTHING HAS BEEN LAUNCHED YET, and that is the point of running both
        # of these first: a broken instrument and an occupied port are both
        # answers that do not need a server to establish, and starting one
        # anyway would leave a process behind for a run that decided nothing.
        return Report(code=verdict, findings=tuple(findings))

    handle: ServerHandle | None = None
    try:
        handle = backends.launch(options.port)
        findings.extend(launch_stage(options, backends, handle))
        if decide(findings) == EXIT_PASS:
            findings.extend(json_stage(options, backends))
            findings.extend(dom_stage(options, backends))
            findings.extend(evidence_stage(options, backends))
    finally:
        findings.extend(cleanup_stage(options, backends, handle))
    return Report(code=decide(findings), findings=tuple(findings))


# ---------------------------------------------------------------------------
# Rendering.
# ---------------------------------------------------------------------------

#: What each exit code is called in the report, so the number never stands alone.
CODE_NAMES: Final = {
    EXIT_PASS: "PASS",
    EXIT_USAGE: "USAGE",
    EXIT_PORT_BUSY: "PORT_BUSY",
    EXIT_LAUNCH: "LAUNCH",
    EXIT_TRANSPORT: "TRANSPORT",
    EXIT_JSON: "JSON",
    EXIT_DOM: "DOM",
    EXIT_CONTROL: "CONTROL",
    EXIT_CLEANUP: "CLEANUP",
}


def render(report: Report) -> str:
    """Render the whole report, verbatim, whatever the verdict.

    EVERY FINDING IS PRINTED INCLUDING THE PASSES. A gate that prints only what
    failed cannot be re-graded from its own output, and cannot be distinguished
    from a gate that asserted nothing.

    Args:
        report: What the run observed.

    Returns:
        The text, without a trailing newline.
    """
    lines = [f"clockspeed dashboard probe - {CODE_NAMES.get(report.code, '?')} ({report.code})", ""]
    for finding in report.findings:
        lines.append(f"  [{finding.verdict:11}] {finding.stage}: {finding.name}")
        lines.append(f"                {finding.detail}")
    lines.append("")
    counted = dict.fromkeys((PASS, FAIL, SKIP, UNAVAILABLE), 0)
    for finding in report.findings:
        counted[finding.verdict] = counted.get(finding.verdict, 0) + 1
    lines.append(
        "  ".join(f"{word}: {number}" for word, number in counted.items())
        + f"   -> exit {report.code} ({CODE_NAMES.get(report.code, '?')})"
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# The real backends. Nothing below this line is reachable from a test.
# ---------------------------------------------------------------------------


def client_context(certificate: Path, *, verify: bool) -> ssl.SSLContext:
    """A client context, pinned to the dashboard's own certificate by default.

    PINNED, NOT DISABLED, and the difference is the whole point. The pair
    ``scripts/make_cert.py`` mints carries an ``IP:127.0.0.1`` SAN, so trusting
    that one file as the CA and connecting to that address verifies with
    ``check_hostname`` left where ``create_default_context`` puts it. This is the
    idiom ``tests/surface/test_server.py`` uses on every arm.

    Args:
        certificate: The certificate the configuration says is being served.
        verify: False to waive verification entirely. See the module docstring:
            a waived run is not evidence about the certificate.

    Returns:
        The context. Either branch pins TLS 1.2, as clockspeed/surface/server.py
        pins its own: the interpreter's default minimum is not TLS 1.2 on every
        build (CS-1338).
    """
    if not verify:
        # WAIVED, NOT CHECKED. Reached only when the operator passed
        # --no-verify, and the report says so on its own face.
        waived = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        waived.minimum_version = ssl.TLSVersion.TLSv1_2
        waived.check_hostname = False
        waived.verify_mode = ssl.CERT_NONE
        return waived
    context = ssl.create_default_context(cafile=str(certificate))
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context


def https_client(
    certificate: Path,
    *,
    verify: bool,
) -> Callable[[int, str, float], Exchange]:
    """Build the fetch backend that really talks to the dashboard.

    Args:
        certificate: The certificate to pin.
        verify: Whether to verify against it.

    Returns:
        A fetch callable taking a port, a path and a deadline.
    """

    def fetch(port: int, path: str, deadline_s: float) -> Exchange:
        """Issue one request to the dashboard over loopback HTTPS.

        Args:
            port: Where the dashboard is listening.
            path: The request path, a literal this repository authored.
            deadline_s: The socket timeout. Bounded: nothing waits forever.

        Returns:
            What came back, or the class name of what stopped it.
        """
        try:
            context = client_context(certificate, verify=verify)
        except OSError as exc:
            # A MISSING OR UNPARSEABLE CERTIFICATE IS A TRANSPORT FACT, not a
            # crash. `cafile` is opened here, so an absent pair lands as an
            # OSError carrying the FILENAME - which is why only the summary is
            # kept (non-negotiable 12).
            return Exchange(status=None, body="", content_type="", error=server.cause_summary(exc))
        connection = http_client.HTTPSConnection(
            config.LOOPBACK, port, timeout=deadline_s, context=context
        )
        try:
            connection.request("GET", path)
            response = connection.getresponse()
            body = response.read().decode("utf-8", errors="replace")
            return Exchange(
                status=response.status,
                body=body,
                content_type=response.headers.get("Content-Type", ""),
                error="",
            )
        except (OSError, http_client.HTTPException) as exc:
            # THE SUMMARY, NEVER THE OBJECT. `OSError.__str__` appends a
            # filename when the interpreter set one, and a filename on this
            # machine can be a home path (non-negotiable 12). `cause_summary`
            # keeps a class name and an integer errno, both safe by
            # construction.
            return Exchange(status=None, body="", content_type="", error=server.cause_summary(exc))
        finally:
            connection.close()

    return fetch


def port_is_bound(port: int) -> bool:
    """True when something is accepting on loopback at that port.

    A CONNECT AND NOT A LISTEN. Binding to test would race the thing being
    tested and would itself hold the port for a moment.

    Args:
        port: The port to probe.

    Returns:
        Whether a connection was accepted.
    """
    connection = http_client.HTTPConnection(config.LOOPBACK, port, timeout=1.0)
    try:
        connection.connect()
    except OSError:
        return False
    else:
        return True
    finally:
        connection.close()


class _ChildServer:
    """The dashboard, running as a child process.

    THE STOP ESCALATES AND EACH RUNG IS BOUNDED. A console break lets the
    server's own SIGINT handler run its documented shutdown, which releases the
    listener cleanly; terminate is the rung for a child that ignored it; and
    ``taskkill /F /T`` is the rung that also reaps the child's children, because
    the pid held here is the interpreter and not necessarily the only process in
    its tree. The PowerShell cmdlet is deliberately not used.
    """

    def __init__(self, process: subprocess.Popen[bytes], rung_s: float, adoption: str) -> None:
        """Wrap a started child.

        Args:
            process: The started process.
            rung_s: How long each rung of the stop gets.
            adoption: What the kill-on-close job object did, verbatim. Carried
                on the handle rather than reported separately so it lands in
                the same line as the stop it is the backstop for.
        """
        self._process = process
        self._rung_s = rung_s
        self._adoption = adoption

    def exit_code(self) -> int | None:
        """The child's exit code, or None while it runs.

        Returns:
            The code, or None.
        """
        return self._process.poll()

    def stop(self) -> str:
        """Stop the child, bounded, and name the rung that worked.

        Returns:
            A one-line account, ending with what the job-object backstop did.
        """
        return f"{self._escalate()}; kill-on-close job object: {self._adoption}"

    def _escalate(self) -> str:
        """Work down the rungs until one of them lands.

        Returns:
            Which rung stopped it, or that none did.
        """
        already = self._process.poll()
        if already is not None:
            return f"already exited {already} before the stop was issued"
        for rung, act in (
            ("console break", self._break),
            ("terminate", self._process.terminate),
            ("taskkill /F /T", self._taskkill),
        ):
            try:
                act()
            except OSError as exc:
                return f"the {rung} rung raised {server.cause_summary(exc)}"
            try:
                code = self._process.wait(timeout=self._rung_s)
            except subprocess.TimeoutExpired:
                continue
            return f"stopped by the {rung} rung; the child exited {exit_reading(code)}"
        return f"still running after every rung, each bounded at {self._rung_s:g}s"

    def _break(self) -> None:
        """Send the console break the child's own handler listens for.

        The child is started in its own process group precisely so this signal
        reaches it and NOT this process. ``signal.CTRL_BREAK_EVENT`` exists only
        on Windows, which is what the guard below is for; elsewhere this rung is
        a no-op and the escalation moves straight on to terminate.
        """
        if os.name != "nt":
            return
        self._process.send_signal(signal.CTRL_BREAK_EVENT)

    def _taskkill(self) -> None:
        """Kill the whole tree, forcibly.

        ``/T`` because the pid held here is the interpreter that ``-m`` started
        and a tree is what has to go. The executable is RESOLVED and never
        spelled (CS-910): a bare name is resolved against the working directory
        first on Windows, and the PowerShell cmdlet is deliberately not used.
        An unresolvable killer is not an error - the rung simply does nothing
        and its bounded wait expires.
        """
        killer = resolve_tool(TASKKILL_NAME)
        if killer is None:
            return
        subprocess.run(
            [killer, "/F", "/T", "/PID", str(self._process.pid)],
            check=False,
            capture_output=True,
            timeout=self._rung_s,
        )


def child_launcher(
    artifact_dir: Path,
    *,
    with_world: bool,
    rung_s: float,
) -> Callable[[int], ServerHandle]:
    """Build the launcher that really starts ``python -m clockspeed.surface``.

    THE INTERPRETER IS ``sys.executable`` AND IS NEVER SPELLED. An absolute
    interpreter path in a tracked file is forbidden outright (BOOTSTRAP.md
    section 2.5), and the running interpreter is the only correct one anyway.
    It is not printed either.

    THE CHILD'S OUTPUT GOES TO A FILE AND NOT TO A PIPE. A pipe nobody drains
    blocks the writer once the buffer fills, and the writer here is the thing
    under test - so the probe would deadlock the server and then report it
    unresponsive. A file cannot fill.

    Args:
        artifact_dir: Where the captured output lands. Gitignored.
        with_world: True to let the child detect a save. Off by default, so the
            page has no world to render and no capture can contain one.
        rung_s: How long each rung of the stop gets.

    Returns:
        A launcher taking a port and returning a handle.
    """

    def launch(port: int) -> ServerHandle:
        """Start the dashboard on a port.

        Args:
            port: The port to bind.

        Returns:
            The handle.
        """
        argv = [sys.executable, "-m", "clockspeed.surface", "--port", str(port)]
        if not with_world:
            argv.append("--no-world")
        artifact_dir.mkdir(parents=True, exist_ok=True)
        sink = artifact_dir / CHILD_OUTPUT_NAME
        stream = sink.open("wb")
        creation = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        process = subprocess.Popen(
            argv,
            cwd=config.repo_root(),
            stdout=stream,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            creationflags=creation,
        )
        adoption = _adopt(process)
        # THE SETTLE WAIT IS AN EARLY-DEATH DETECTOR AND A BOUND IN ITS OWN
        # RIGHT. A child that refuses at once - no certificate, a port taken
        # between the probe and the bind - is reported here rather than after a
        # full launch deadline spent polling a socket nothing is behind. It is
        # also where this handle's Popen is bounded in the scope that created
        # it; the escalating stop bounds it again, later and harder.
        with contextlib.suppress(subprocess.TimeoutExpired):
            process.wait(timeout=SETTLE_S)
        return _ChildServer(process, rung_s, adoption)

    return launch


def _adopt(process: subprocess.Popen[bytes]) -> str:
    """Bind the child to a kill-on-close job object, best effort.

    THE MECHANISM FOR THE ONE CASE A ``finally`` CANNOT COVER. A probe that is
    killed rather than unwound never runs its cleanup, and the listener it
    started would then outlive it and meet the next run as a busy port. A
    Windows job object marked ``KILL_ON_JOB_CLOSE`` is reaped BY THE KERNEL when
    the last handle to it closes, which happens when this process dies however
    it dies.

    BEST EFFORT AND REPORTED AS SUCH. A box that refuses the job object still
    gets the other three mechanisms; what it does not get is a silent claim that
    it had four.

    Args:
        process: The started child.

    Returns:
        Empty when the child was adopted, or a short reason when it was not.
    """
    if os.name != "nt":
        return "not applicable off Windows"
    handle = getattr(process, "_handle", None)
    if handle is None:
        return "the child exposes no OS handle to assign"
    try:
        return _assign_to_job(int(handle))
    except (OSError, AttributeError, ValueError) as exc:
        # THE SUMMARY, NEVER THE OBJECT (non-negotiable 12), and a broad catch
        # on purpose: this is a backstop, so every way it can fail has to end in
        # a reported degradation rather than in a raise that fails the run over
        # a mechanism the run does not depend on.
        return f"refused with {server.cause_summary(exc)}"


def _assign_to_job(handle: int) -> str:
    """Create the kill-on-close job and put one process handle in it.

    Args:
        handle: The child's OS process handle.

    Returns:
        ``adopted``, or which call refused.
    """
    import ctypes  # noqa: PLC0415 - Windows-only, so it is looked up at call time

    kernel = ctypes.windll.kernel32
    job = kernel.CreateJobObjectW(None, None)
    if not job:
        return "CreateJobObject refused"
    limits = bytearray(JOB_LIMIT_STRUCT_BYTES)
    limits[JOB_LIMIT_FLAGS_OFFSET : JOB_LIMIT_FLAGS_OFFSET + 4] = JOB_KILL_ON_CLOSE.to_bytes(
        4, "little"
    )
    buffer = (ctypes.c_char * len(limits)).from_buffer(limits)
    if not kernel.SetInformationJobObject(job, JOB_EXTENDED_LIMIT_CLASS, buffer, len(limits)):
        return "SetInformationJobObject refused"
    if not kernel.AssignProcessToJobObject(job, handle):
        return "AssignProcessToJobObject refused"
    _JOBS.append(job)
    return "adopted"


def _unwired(port: int, path: str, deadline_s: float) -> Exchange:
    """The bridge's default upstream, which refuses rather than guessing.

    A CLASS ATTRIBUTE HAS TO HAVE A VALUE, and the honest value for "nobody
    wired this yet" is a refusal. The alternative - defaulting to a real client
    - would let a bridge built wrong forward somewhere by accident.

    Args:
        port: Ignored.
        path: Ignored.
        deadline_s: Ignored.

    Returns:
        A failed exchange naming the reason.
    """
    del port, path, deadline_s
    return Exchange(status=None, body="", content_type="", error="the bridge was not wired")


class _BridgeHandler(http_server.BaseHTTPRequestHandler):
    """Re-issue one plain-HTTP request to the dashboard over HTTPS.

    THE BRIDGE EXISTS BECAUSE NO AUTOMATION BROWSER ON THIS BOX WILL LOAD THE
    DASHBOARD'S SELF-SIGNED CERTIFICATE - measured, more than once. It listens on
    loopback only, on a port the operating system chose, for the duration of one
    screenshot. It takes no allocation from ``config/ports.json``, because that
    record allocates ports for services something else has to FIND.
    """

    #: Set by the subclass the factory below builds.
    target_port: int = 0
    request_deadline_s: float = REQUEST_DEADLINE_S
    fetch: Callable[[int, str, float], Exchange] = staticmethod(_unwired)

    def do_GET(self) -> None:
        """Forward this request and copy the answer back."""
        exchange = type(self).fetch(self.target_port, self.path, self.request_deadline_s)
        if exchange.error or exchange.status is None:
            self.send_response(contract.HTTP_UNAVAILABLE)
            self.end_headers()
            return
        body = exchange.body.encode("utf-8")
        try:
            self.send_response(exchange.status)
            if exchange.content_type:
                self.send_header("Content-Type", exchange.content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except OSError:
            # A BROWSER ABANDONING A REQUEST IS NORMAL AND IS NEVER A FINDING.
            # Headless Chrome drops connections it already has the bytes for,
            # and the unhandled version of this printed a full traceback - see
            # the server class below for why that is a privacy fault and not
            # merely noise.
            return

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002 - base class name
        """Log nothing.

        The base class writes every request line to stderr, and a request line
        is caller-chosen text. This bridge is up for one screenshot; a request
        log from it is noise at best.

        Args:
            format: The base class's format string, unused.
            args: Its arguments, unused.
        """
        del format, args


class BridgeServer(http_server.ThreadingHTTPServer):
    """The loopback forwarder, silent about its own transport faults.

    THE BASE CLASS PRINTS A TRACEBACK, AND A TRACEBACK SPELLS ABSOLUTE PATHS.
    MEASURED on this box during the first real run of this gate: headless Chrome
    aborted a connection mid-write, ``socketserver`` printed the stack, and the
    frames named this machine's home directory on the gate's OWN stderr - a home
    path in an echo path, which is non-negotiables 3 and 12 in the one place
    nobody thinks to look, because the run was otherwise green.

    So this server reports nothing about its own connections. It is scaffolding
    for a screenshot; it is not the subject, and it can say nothing about the
    subject that the deciding legs have not already said.
    """

    daemon_threads = True

    def handle_error(self, request: object, client_address: object) -> None:
        """Say nothing when a connection dies mid-answer.

        Args:
            request: The socket, unused.
            client_address: The peer, unused - and deliberately never rendered.
        """
        del request, client_address


def browser_path(declared: str | None = None) -> str:
    """Find a browser that can render headlessly, or return empty.

    NO ABSOLUTE PATH IS SPELLED IN THIS FILE. PATH is asked first - through
    ``tools/toolpath.py`` and NOT through ``shutil.which``, which resolves
    against the working directory on Windows and is the defect CS-910 exists to
    remove - and then the location the ENVIRONMENT names for installed programs,
    because a browser is rarely on PATH on Windows. A box with neither is a box
    where the capture leg degrades, which is exactly what it is built to do.

    Args:
        declared: What the operator named, or None to search.

    Returns:
        The executable, or empty when there is none.
    """
    if declared:
        return declared
    for name in BROWSER_NAMES:
        found = resolve_tool(name)
        if found:
            return found
    for variable in PROGRAM_FILES_ENV:
        root = os.environ.get(variable)
        if not root:
            continue
        for suffix in BROWSER_SUFFIXES:
            candidate = Path(root).joinpath(*suffix)
            if candidate.is_file():
                return str(candidate)
    return ""


def screenshot_capture(
    artifact_dir: Path,
    repo_root: Path,
    executable: str,
    upstream: Callable[[int, str, float], Exchange],
    deadline_s: float = CAPTURE_DEADLINE_S,
) -> Callable[[int], Capture]:
    """Build the capture backend: bridge to plain HTTP, then shoot it.

    Args:
        artifact_dir: Where the PNG and the throwaway profile land.
        repo_root: What the reported path is made relative to.
        executable: The browser found by :func:`browser_path`.
        upstream: The HTTPS client the bridge forwards through, so the capture
            leg reaches the dashboard exactly the way the deciding legs do.
        deadline_s: How long the browser gets. Bounded.

    Returns:
        A capture backend taking the dashboard's port.
    """

    def capture(port: int) -> Capture:
        """Screenshot the dashboard through a plain-HTTP bridge.

        Args:
            port: Where the dashboard is listening.

        Returns:
            What happened.
        """
        artifact_dir.mkdir(parents=True, exist_ok=True)
        destination = artifact_dir / CAPTURE_NAME
        profile = artifact_dir / BROWSER_PROFILE_NAME
        shown = _relative(destination, repo_root)
        handler = type(
            "_BoundBridgeHandler",
            (_BridgeHandler,),
            {
                "target_port": port,
                "request_deadline_s": REQUEST_DEADLINE_S,
                "fetch": staticmethod(upstream),
            },
        )
        bridge = BridgeServer((config.LOOPBACK, 0), handler)
        thread = threading.Thread(target=bridge.serve_forever, daemon=True, name="probe-bridge")
        thread.start()
        try:
            url = f"http://{config.LOOPBACK}:{bridge.server_address[1]}{DOCUMENT_PATH}"
            completed = subprocess.run(
                [
                    executable,
                    "--headless=new",
                    "--disable-gpu",
                    "--no-first-run",
                    "--no-default-browser-check",
                    f"--user-data-dir={profile}",
                    f"--window-size={CAPTURE_WIDTH},{CAPTURE_HEIGHT}",
                    f"--virtual-time-budget={CAPTURE_SETTLE_MS}",
                    f"--screenshot={destination}",
                    url,
                ],
                check=False,
                capture_output=True,
                timeout=deadline_s,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return Capture(taken=False, where="", reason=f"the browser {_why(exc)}")
        finally:
            bridge.shutdown()
            bridge.server_close()
        if not destination.is_file() or destination.stat().st_size == 0:
            return Capture(
                taken=False,
                where="",
                reason=f"the browser exited {completed.returncode} and wrote no image",
            )
        return Capture(taken=True, where=shown, reason="")

    return capture


def _why(exc: BaseException) -> str:
    """Summarise a failure without rendering it.

    Args:
        exc: The failure.

    Returns:
        A class name, and an errno when there is one.
    """
    if isinstance(exc, subprocess.TimeoutExpired):
        return "did not finish inside its deadline"
    return f"failed with {server.cause_summary(exc)}"


def _relative(path: Path, root: Path) -> str:
    """Render a path relative to the repository, or by name alone.

    AN ABSOLUTE PATH IS NEVER RETURNED. The repository could sit anywhere,
    including under a home directory, and this string is printed
    (non-negotiable 3).

    Args:
        path: The path to render.
        root: The repository root.

    Returns:
        The relative path, or the filename when it is outside the repository.
    """
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


# ---------------------------------------------------------------------------
# The command line.
# ---------------------------------------------------------------------------

PROGRAM: Final = "python tools/dashboard_probe.py"

_DESCRIPTION: Final = (
    "Launch the local dashboard, assert a named JSON key and a named DOM node "
    "against it, capture one screenshot, stop it, and decide by exit code."
)

EPILOG: Final = (
    "Exit codes: 0 pass, 1 usage, 2 port already busy, 3 launch, 4 transport, "
    "5 json, 6 dom, 7 control (the run measured nothing), 8 cleanup. "
    "The screenshot NEVER decides: with no browser automation on this box it "
    "reports 'screenshot: unavailable' with the reason and the JSON and DOM "
    "assertions still decide. The port must be free - this probe starts the "
    "server it grades and refuses to measure one it did not start. Mint the "
    "certificate with scripts/make_cert.py first, or the child exits 3."
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the operator's arguments.

    Args:
        argv: The arguments, or None for ``sys.argv[1:]``.

    Returns:
        The parsed namespace.
    """
    parser = argparse.ArgumentParser(prog=PROGRAM, description=_DESCRIPTION, epilog=EPILOG)
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="the port to launch on and poll; defaults to the allocation record",
    )
    parser.add_argument(
        "--no-screenshot",
        dest="screenshot",
        action="store_false",
        default=True,
        help="skip the capture leg entirely",
    )
    parser.add_argument(
        "--with-world",
        action="store_true",
        default=False,
        help=(
            "let the child detect a save. OFF by default: a rendered world puts a "
            "world name in the screenshot, which is personal data"
        ),
    )
    parser.add_argument(
        "--browser",
        default=None,
        help="the browser executable for the capture leg; searched when omitted",
    )
    parser.add_argument(
        "--no-verify",
        dest="verify",
        action="store_false",
        default=True,
        help=(
            "WAIVE TLS verification instead of pinning the dashboard's own "
            "certificate. A run that uses this is not evidence about the certificate"
        ),
    )
    return parser.parse_args(argv)


def build_options(parsed: argparse.Namespace, root: Path) -> Options:
    """Turn parsed arguments into the frozen options.

    Args:
        parsed: What argparse produced.
        root: The repository root.

    Returns:
        The options.
    """
    return Options(
        port=config.allocated_port() if parsed.port is None else parsed.port,
        with_world=bool(parsed.with_world),
        verify=bool(parsed.verify),
        screenshot=bool(parsed.screenshot),
        artifact_dir=root.joinpath(*ARTIFACT_PARTS),
    )


def build_backends(options: Options, root: Path, browser: str, certificate: Path) -> Backends:
    """Wire the real effects.

    Args:
        options: What the operator asked for.
        root: The repository root.
        browser: The browser executable, or empty when there is none.
        certificate: The certificate the configuration says is being served.

    Returns:
        The backends.
    """
    fetch = https_client(certificate, verify=options.verify)
    return Backends(
        launch=child_launcher(
            options.artifact_dir, with_world=options.with_world, rung_s=options.stop_deadline_s
        ),
        fetch=fetch,
        port_bound=port_is_bound,
        clock=time.monotonic,
        sleep=time.sleep,
        capture=(
            screenshot_capture(options.artifact_dir, root, browser, fetch)
            if browser and options.screenshot
            else None
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run one probe and return its exit code.

    Args:
        argv: The arguments, or None for ``sys.argv[1:]``.

    Returns:
        One of the module's exit codes.
    """
    try:
        parsed = parse_args(argv)
    except SystemExit as exit_request:
        # ARGPARSE EXITS 2 ON A BAD INVOCATION, and 2 is PORT_BUSY here. A gate
        # whose codes overlap is a gate no runbook can branch on, so the one
        # argparse chose is remapped and only its --help zero is let through.
        if exit_request.code in (0, None):
            raise
        return EXIT_USAGE

    root = config.repo_root()
    options = build_options(parsed, root)
    try:
        certificate = config.load_config(requested_port=options.port).cert_path
    except config.ConfigError as exc:
        # THE NAMED FIELD, NEVER THE OBJECT. `config_refusal` maps a closed
        # fault enum to text that module owns; `str(exc)` would render whatever
        # the caught object turns out to be. This is the idiom
        # clockspeed/surface/__main__.py already uses at the same seam.
        print(f"the configuration would not resolve: {config.config_refusal(exc.fault)}")
        return EXIT_USAGE
    backends = build_backends(options, root, browser_path(parsed.browser), certificate)
    report = probe(options, backends)
    print(render(report))
    return report.code


if __name__ == "__main__":
    sys.exit(main())
