"""CS-918 - the dashboard gate decides by exit code, and the code has to be right.

WHAT THIS MODULE GRADES. ``tools/dashboard_probe.py`` exists to replace a
judgment call with a procedure, so the thing worth grading is not "does it
print PASS" but "does it reach the RIGHT code for each distinct condition". A
gate that collapsed a launch failure into an assertion failure would still be
green on the happy path and would still be useless, because the whole reason it
exists is that a reader must be able to tell those two apart.

NOTHING HERE SPAWNS A PROCESS, BINDS A PORT, SLEEPS OR SHELLS OUT. Every
external effect is injected through ``Backends``, including the CLOCK - the
probe's deadlines are grade-able only if a test can move time without waiting
for it. The suite therefore runs on a machine with no game installed, nothing
listening on any port and no browser, which is the machine the rule suite has to
run on (BOOTSTRAP.md section 5.4).

THE TWO INSTRUMENTS ARE INJECTED FOR ONE SPECIFIC REASON. ``find_ids`` and
``read_path`` are what the verdict is measured WITH. Substituting a broken one
is the only way to prove the control catches a broken instrument, and a control
nothing has ever seen fail is a control nobody should trust. The two arms named
``..._is_a_control_failure_and_not_a_..._failure`` are the point of the file.
"""

from __future__ import annotations

import json
import socketserver
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Final

import pytest

from clockspeed.surface import config, server
from clockspeed.surface.api import contract, health

REPO_ROOT: Final = Path(__file__).resolve().parents[1]

# tools/ joins the path so the module under test is imported under the SAME bare
# name every other importer uses. `tools` carries no __init__.py, so the
# `tools.dashboard_probe` spelling would hand mypy the same file under two module
# names and it refuses the run. This is tests/test_toolpath.py's idiom, verbatim.
_TOOLS_DIR: Final = REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import dashboard_probe as probe_module  # noqa: E402

# ---------------------------------------------------------------------------
# Fakes. Every one of them is a seam the module publishes.
# ---------------------------------------------------------------------------

#: A port the fakes agree on. NOT the allocated one, and deliberately outside
#: the band ``config/ports.json`` owns - nothing here binds anything, and a test
#: that spelled the real allocation would be a second copy of a number that file
#: is the single owner of.
FAKE_PORT: Final = 1

# The seam shapes, named once. Spelled here rather than inline so a fake that
# drifts from the real signature is a type error at its own definition rather
# than an argument error inside a helper.
Launcher = Callable[[int], "probe_module.ServerHandle"]
PortProbe = Callable[[int], bool]
Capturer = Callable[[int], "probe_module.Capture"]
Finder = Callable[[str], "frozenset[str]"]
Reader = Callable[[object, "tuple[str, ...]"], "tuple[bool, object]"]


@dataclass
class FakeHandle:
    """A child process that never existed.

    Attributes:
        code: What ``exit_code`` reports. None means still running.
        stopped: How many times ``stop`` was called.
        account: What ``stop`` returns - PROSE, which is why the probe does not
            grade it. The structural question is whether an exit code appears.
        code_after_stop: What ``exit_code`` reports once ``stop`` has run. None
            models a child that survived every rung.
    """

    code: int | None = None
    stopped: int = 0
    account: str = "stopped by the console break rung; the child exited 0"
    code_after_stop: int | None = 0

    def exit_code(self) -> int | None:
        """The child's exit code, or None.

        Returns:
            The code.
        """
        return self.code

    def stop(self) -> str:
        """Record the stop and report how it went.

        Returns:
            The account.
        """
        self.stopped += 1
        self.code = self.code_after_stop
        return self.account


@dataclass
class FakeClock:
    """A monotonic clock a test drives.

    Attributes:
        now: The current reading.
        step: How far ``sleep`` advances it.
    """

    now: float = 0.0
    step: float = 1.0

    def read(self) -> float:
        """The current reading.

        Returns:
            The time.
        """
        return self.now

    def sleep(self, seconds: float) -> None:
        """Advance without waiting.

        Args:
            seconds: How far to advance. The probe's own poll interval, which
                is why nothing here has to sleep for real.
        """
        self.now += seconds or self.step


def health_body(
    *,
    liveness: str = health.LIVE,
    status: str = contract.STATUS_OK,
    drop: Iterable[str] = (),
) -> str:
    """A health body of the shape the real endpoint produces.

    BUILT FROM THE ENDPOINT'S OWN CONSTANTS. A hand-typed body would be a second
    copy of the envelope and would keep passing after the real one changed.

    Args:
        liveness: What ``data.endpoints[/api/health]`` says.
        status: The envelope status.
        drop: Top-level ``data`` keys to omit, for the absent-key arms.

    Returns:
        The serialized body.
    """
    data: dict[str, object] = {
        "app_version": "0.0.0",
        "game_build_pin": "build",
        "registry": health.ABSENT,
        "world": health.ABSENT,
        "endpoints": dict.fromkeys(health.ENDPOINT_TEMPLATES, health.NOT_LIVE)
        | {health.ENDPOINT: liveness},
    }
    for key in drop:
        data.pop(key, None)
    return json.dumps({"status": status, "endpoint": health.ENDPOINT, "data": data})


def document(*, ids: Iterable[str] | None = None) -> str:
    """A served page declaring the given ids.

    Args:
        ids: The ids to declare, defaulting to every one the probe requires.

    Returns:
        The markup.
    """
    declared = probe_module.REQUIRED_NODE_IDS if ids is None else tuple(ids)
    nodes = "".join(f'<div id="{name}"></div>' for name in declared)
    return f"<!doctype html><html><body>{nodes}</body></html>"


def ok_exchange(body: str, content_type: str) -> probe_module.Exchange:
    """A completed 200.

    Args:
        body: The body.
        content_type: The declared type.

    Returns:
        The exchange.
    """
    return probe_module.Exchange(
        status=contract.HTTP_OK, body=body, content_type=content_type, error=""
    )


def dead_exchange(error: str = "OSError 10061") -> probe_module.Exchange:
    """An exchange that never completed.

    Args:
        error: The summary, in the shape ``cause_summary`` produces.

    Returns:
        The exchange.
    """
    return probe_module.Exchange(status=None, body="", content_type="", error=error)


@dataclass
class FakeWire:
    """A scripted HTTP client, keyed by request path.

    Attributes:
        answers: Path to exchange.
        asked: Every path asked, in order.
        raises: A failure to throw instead of answering, modelling the gate
            itself breaking rather than the dashboard failing an assertion.
    """

    answers: dict[str, probe_module.Exchange] = field(default_factory=dict)
    asked: list[str] = field(default_factory=list)
    raises: RuntimeError | None = None

    def fetch(self, port: int, path: str, deadline_s: float) -> probe_module.Exchange:
        """Answer one request from the script.

        Args:
            port: Ignored - nothing is bound.
            path: The request path.
            deadline_s: Ignored.

        Returns:
            The scripted exchange, or a dead one for an unscripted path.

        Raises:
            RuntimeError: When this wire was built to throw.
        """
        del port, deadline_s
        self.asked.append(path)
        if self.raises is not None:
            raise self.raises
        return self.answers.get(path, dead_exchange("no answer was scripted"))


def html_type() -> str:
    """The content type the server declares for the page.

    Returns:
        The type, read from the server's own static table.
    """
    return server.STATIC_ROUTES[probe_module.DOCUMENT_PATH][1]


def wired(
    *,
    body: str | None = None,
    page: str | None = None,
    health_exchange: probe_module.Exchange | None = None,
    page_exchange: probe_module.Exchange | None = None,
) -> FakeWire:
    """A wire that answers both paths the probe asks for.

    Args:
        body: The health body, or None for a good one.
        page: The served page, or None for a good one.
        health_exchange: A whole exchange to use for health, overriding ``body``.
        page_exchange: A whole exchange to use for the page, overriding ``page``.

    Returns:
        The wire.
    """
    return FakeWire(
        {
            probe_module.HEALTH_PATH: health_exchange
            or ok_exchange(body if body is not None else health_body(), server.CONTENT_TYPE_JSON),
            probe_module.DOCUMENT_PATH: page_exchange
            or ok_exchange(page if page is not None else document(), html_type()),
        }
    )


def backends(
    wire: FakeWire,
    handle: FakeHandle,
    clock: FakeClock,
    *,
    launch: Launcher | None = None,
    port_bound: PortProbe | None = None,
    capture: Capturer | None = None,
    find_ids: Finder | None = None,
    read_path: Reader | None = None,
) -> probe_module.Backends:
    """Assemble the injected effects for one arm.

    EVERY SEAM IS A NAMED, TYPED PARAMETER rather than a ``**kwargs`` splat into
    ``dataclasses.replace``. The splat came first and the type checker refused
    it, correctly: it accepted ``find_ids=3`` as readily as a finder, which is
    the exact class of mistake the control arms below exist to catch. A helper
    that cannot be checked is a helper that hides a broken fake.

    Args:
        wire: The scripted client.
        handle: The child that never existed.
        clock: The clock the test drives.
        launch: A launcher, or None for one handing back ``handle``.
        port_bound: A port probe, or None for one saying nothing is bound.
        capture: A screenshot backend, or None for a box with no browser.
        find_ids: The id finder, or None for the real one. Broken deliberately
            by the control arms.
        read_path: The key-path reader, or None for the real one.

    Returns:
        The backends.
    """
    return probe_module.Backends(
        launch=launch if launch is not None else (lambda _port: handle),
        fetch=wire.fetch,
        port_bound=port_bound if port_bound is not None else (lambda _port: False),
        clock=clock.read,
        sleep=clock.sleep,
        capture=capture,
        find_ids=find_ids if find_ids is not None else probe_module.document_ids,
        read_path=read_path if read_path is not None else probe_module.follow_path,
    )


def options(
    *,
    node_ids: tuple[str, ...] | None = None,
    with_world: bool = False,
    verify: bool = True,
    screenshot: bool = True,
) -> probe_module.Options:
    """Options for one arm.

    Args:
        node_ids: The required ids, or None for the probe's own set.
        with_world: Whether the child would detect a save.
        verify: Whether TLS verification is on.
        screenshot: Whether the capture leg is asked for.

    Returns:
        The options.
    """
    base = probe_module.Options(port=FAKE_PORT)
    return replace(
        base,
        node_ids=base.node_ids if node_ids is None else node_ids,
        with_world=with_world,
        verify=verify,
        screenshot=screenshot,
    )


def run(
    *,
    wire: FakeWire | None = None,
    handle: FakeHandle | None = None,
    clock: FakeClock | None = None,
    launch: Launcher | None = None,
    port_bound: PortProbe | None = None,
    capture: Capturer | None = None,
    find_ids: Finder | None = None,
    read_path: Reader | None = None,
) -> probe_module.Report:
    """Run one whole probe against fakes.

    Args:
        wire: The scripted client, or None for a good one.
        handle: The child, or None for one that stays up.
        clock: The clock, or None for a fresh one.
        launch: A launcher, or None for one handing back ``handle``.
        port_bound: A port probe, or None for one saying nothing is bound.
        capture: A screenshot backend, or None for a box with no browser.
        find_ids: The id finder, or None for the real one.
        read_path: The key-path reader, or None for the real one.

    Returns:
        The report.
    """
    return probe_module.probe(
        options(),
        backends(
            wire or wired(),
            handle or FakeHandle(),
            clock or FakeClock(),
            launch=launch,
            port_bound=port_bound,
            capture=capture,
            find_ids=find_ids,
            read_path=read_path,
        ),
    )


def stages_that_failed(report: probe_module.Report) -> set[str]:
    """Which stages carry a failing finding.

    Args:
        report: The report.

    Returns:
        The stage names.
    """
    return {f.stage for f in report.findings if f.verdict == probe_module.FAIL}


# ---------------------------------------------------------------------------
# The control. These two arms are why this module exists.
# ---------------------------------------------------------------------------


def test_a_blind_node_finder_is_a_control_failure_and_not_a_dom_failure() -> None:
    report = run(find_ids=lambda _text: frozenset())
    assert report.code == probe_module.EXIT_CONTROL, (
        "a finder that sees nothing must invalidate the measurement, not condemn "
        f"the dashboard; the report reached {report.code} with stages "
        f"{sorted(stages_that_failed(report))}"
    )


def test_a_rubber_stamp_node_finder_is_a_control_failure() -> None:
    every = frozenset({*probe_module.REQUIRED_NODE_IDS, probe_module.DOM_CONTROL_ABSENT})
    report = run(find_ids=lambda _text: every)
    assert report.code == probe_module.EXIT_CONTROL


def test_a_blind_key_reader_is_a_control_failure_and_not_a_json_failure() -> None:
    report = run(read_path=lambda _payload, _path: (False, None))
    assert report.code == probe_module.EXIT_CONTROL


def test_a_rubber_stamp_key_reader_is_a_control_failure() -> None:
    report = run(read_path=lambda _payload, _path: (True, health.LIVE))
    assert report.code == probe_module.EXIT_CONTROL


def test_the_static_control_runs_before_anything_is_launched() -> None:
    launched: list[int] = []

    def launch(port: int) -> probe_module.ServerHandle:
        launched.append(port)
        return FakeHandle()

    report = run(find_ids=lambda _text: frozenset(), launch=launch)
    assert (report.code, launched) == (probe_module.EXIT_CONTROL, [])


def test_the_control_document_and_payload_really_exercise_both_directions() -> None:
    found = probe_module.document_ids(probe_module.CONTROL_DOCUMENT)
    hit, _value = probe_module.follow_path(
        probe_module.CONTROL_PAYLOAD, probe_module.JSON_STATIC_PRESENT
    )
    miss, _absent = probe_module.follow_path(
        probe_module.CONTROL_PAYLOAD, probe_module.JSON_STATIC_ABSENT
    )
    assert (
        probe_module.DOM_CONTROL_PRESENT in found,
        probe_module.DOM_CONTROL_ABSENT in found,
        hit,
        miss,
    ) == (True, False, True, False)


def test_the_live_control_names_a_template_the_surface_does_not_publish() -> None:
    absent = probe_module.JSON_CONTROL_ABSENT[-1]
    assert absent not in health.ENDPOINT_TEMPLATES


# ---------------------------------------------------------------------------
# Launch, and the conditions that are NOT assertion failures.
# ---------------------------------------------------------------------------


def test_a_busy_port_refuses_before_anything_is_launched() -> None:
    launched: list[int] = []

    def launch(port: int) -> probe_module.ServerHandle:
        launched.append(port)
        return FakeHandle()

    report = run(port_bound=lambda _port: True, launch=launch)
    assert (report.code, launched) == (probe_module.EXIT_PORT_BUSY, [])


def test_a_server_that_never_answers_is_a_launch_failure_not_an_assertion_failure() -> None:
    wire = FakeWire({})
    report = run(wire=wire, clock=FakeClock(step=1.0))
    assert report.code == probe_module.EXIT_LAUNCH, (
        "a socket nothing is behind must not be filed as a content defect; the "
        f"report reached {report.code}"
    )


def test_a_launch_failure_is_bounded_by_the_injected_clock() -> None:
    clock = FakeClock(step=1.0)
    run(wire=FakeWire({}), clock=clock)
    assert clock.now >= probe_module.LAUNCH_DEADLINE_S


def test_a_child_that_exits_early_is_a_launch_failure_naming_its_exit_code() -> None:
    handle = FakeHandle(code=server.EXIT_CERTIFICATE)
    report = run(wire=FakeWire({}), handle=handle)
    rendered = probe_module.render(report)
    assert (report.code, f"exited {server.EXIT_CERTIFICATE}" in rendered) == (
        probe_module.EXIT_LAUNCH,
        True,
    )


def test_the_child_is_stopped_even_when_it_never_answered() -> None:
    handle = FakeHandle()
    run(wire=FakeWire({}), handle=handle)
    assert handle.stopped == 1


# ---------------------------------------------------------------------------
# Content.
# ---------------------------------------------------------------------------


def test_a_missing_json_key_is_a_json_failure() -> None:
    report = run(wire=wired(body=health_body(drop=["endpoints"])))
    assert report.code == probe_module.EXIT_JSON


def test_a_wrong_liveness_word_is_a_json_failure() -> None:
    report = run(wire=wired(body=health_body(liveness=health.NOT_LIVE)))
    assert report.code == probe_module.EXIT_JSON


def test_a_body_that_is_not_json_is_a_json_failure_and_never_echoes_it() -> None:
    unparseable = "not json at all, and this text must not be reprinted"
    report = run(wire=wired(body=unparseable))
    rendered = probe_module.render(report)
    assert (report.code, unparseable in rendered) == (probe_module.EXIT_JSON, False)


def test_a_renamed_dom_node_is_a_dom_failure_naming_the_node() -> None:
    missing = probe_module.REQUIRED_NODE_IDS[0]
    kept = probe_module.REQUIRED_NODE_IDS[1:]
    report = run(wire=wired(page=document(ids=kept)))
    rendered = probe_module.render(report)
    assert (report.code, f'id="{missing}"' in rendered) == (probe_module.EXIT_DOM, True)


def test_a_json_failure_outranks_a_dom_failure() -> None:
    report = run(
        wire=wired(body=health_body(drop=["endpoints"]), page=document(ids=())),
    )
    assert (report.code, stages_that_failed(report)) == (probe_module.EXIT_JSON, {"json", "dom"})


def test_a_dead_page_fetch_is_a_transport_failure_not_a_dom_failure() -> None:
    report = run(wire=wired(page_exchange=dead_exchange()))
    assert report.code == probe_module.EXIT_TRANSPORT


def test_a_non_200_health_answer_is_a_json_failure_not_a_transport_failure() -> None:
    refusal = probe_module.Exchange(
        status=contract.HTTP_UNAVAILABLE,
        body=health_body(),
        content_type=server.CONTENT_TYPE_JSON,
        error="",
    )
    report = run(wire=wired(health_exchange=refusal))
    assert report.code == probe_module.EXIT_JSON


def test_the_pass_path_reports_the_key_and_the_node_verbatim() -> None:
    report = run()
    rendered = probe_module.render(report)
    shown = (
        report.code == probe_module.EXIT_PASS
        and f'data.endpoints["{health.ENDPOINT}"]' in rendered
        and f'found "{health.LIVE}"' in rendered
        and f'id="{probe_module.REQUIRED_NODE_IDS[0]}"' in rendered
        and f"HTTP {contract.HTTP_OK}" in rendered
    )
    assert shown, f"the report did not carry what it asserted:\n{rendered}"


# ---------------------------------------------------------------------------
# Cleanup, and the one path a finally has to cover.
# ---------------------------------------------------------------------------


def test_the_child_is_stopped_when_a_backend_raises() -> None:
    handle = FakeHandle()
    wire = FakeWire(raises=RuntimeError("the gate itself broke"))
    with pytest.raises(RuntimeError):
        probe_module.probe(options(), backends(wire, handle, FakeClock()))
    assert handle.stopped == 1


def test_a_server_that_will_not_stop_is_a_cleanup_failure() -> None:
    handle = FakeHandle(
        account="still running after every rung, each bounded at 5s", code_after_stop=None
    )
    report = run(handle=handle, port_bound=lambda _port: False)
    assert report.code == probe_module.EXIT_CLEANUP


def test_a_port_still_bound_after_the_stop_is_a_cleanup_failure() -> None:
    seen: list[int] = []

    def bound(port: int) -> bool:
        seen.append(port)
        return len(seen) > 1

    report = run(port_bound=bound)
    assert report.code == probe_module.EXIT_CLEANUP


def test_a_content_failure_outranks_a_cleanup_failure() -> None:
    handle = FakeHandle(
        account="still running after every rung, each bounded at 5s", code_after_stop=None
    )
    report = run(handle=handle, wire=wired(body=health_body(drop=["endpoints"])))
    assert report.code == probe_module.EXIT_JSON


# ---------------------------------------------------------------------------
# The screenshot, which degrades and never decides.
# ---------------------------------------------------------------------------


def test_the_screenshot_degrades_when_no_backend_is_available() -> None:
    report = run()
    evidence = [f for f in report.findings if f.stage == probe_module.STAGE_EVIDENCE]
    verdicts = [f.verdict for f in evidence]
    assert (report.code, verdicts) == (probe_module.EXIT_PASS, [probe_module.UNAVAILABLE])


def test_a_failed_capture_never_decides_the_exit_code() -> None:
    refused = probe_module.Capture(taken=False, where="", reason="the browser wrote no image")
    report = run(capture=lambda _port: refused)
    assert report.code == probe_module.EXIT_PASS


def test_a_capture_reports_a_repository_relative_path_and_says_what_it_is() -> None:
    taken = probe_module.Capture(taken=True, where="data/dashboard_probe/dashboard.png", reason="")
    report = run(capture=lambda _port: taken)
    rendered = probe_module.render(report)
    named = ("PERSONAL-DATA-BEARING" in rendered, "data/dashboard_probe" in rendered)
    assert named == (True, True)


# ---------------------------------------------------------------------------
# Properties of the gate itself.
# ---------------------------------------------------------------------------


def test_an_opaque_windows_status_is_rendered_rather_than_left_as_digits() -> None:
    control_c = 0xC000013A
    reading = probe_module.exit_reading(control_c)
    said = (str(control_c) in reading, "CONTROL_C" in reading)
    assert said == (True, True), (
        "the first real run of this gate printed 3221225786 and nothing else, "
        f"which nobody can re-grade; it now reads {reading!r}"
    )


def test_an_exit_code_this_module_does_not_know_is_still_reported() -> None:
    assert probe_module.exit_reading(77) == "77"


def test_the_bridge_reports_nothing_about_its_own_connections() -> None:
    # MEASURED: headless Chrome aborted a connection mid-write and the base
    # class printed a traceback whose frames named this machine's home
    # directory, on the gate's own stderr. handle_error must be a sink.
    silenced = probe_module.BridgeServer.handle_error
    assert silenced is not socketserver.BaseServer.handle_error


def test_every_exit_code_is_distinct() -> None:
    codes = [
        probe_module.EXIT_PASS,
        probe_module.EXIT_USAGE,
        probe_module.EXIT_PORT_BUSY,
        probe_module.EXIT_LAUNCH,
        probe_module.EXIT_TRANSPORT,
        probe_module.EXIT_JSON,
        probe_module.EXIT_DOM,
        probe_module.EXIT_CONTROL,
        probe_module.EXIT_CLEANUP,
    ]
    assert len(set(codes)) == len(codes)


def test_a_bad_invocation_does_not_collide_with_a_stage_code() -> None:
    outcome = probe_module.main(["--no-such-flag"])
    assert outcome == probe_module.EXIT_USAGE


def probe_source() -> str:
    """The probe module's own text, for the two arms that sweep it.

    Returns:
        The source.
    """
    return (_TOOLS_DIR / "dashboard_probe.py").read_text(encoding="utf-8")


def test_the_probe_source_spells_no_port_in_the_allocated_band() -> None:
    record = json.loads(config.ports_record_path().read_text(encoding="utf-8"))
    band = range(record["band"]["start"], record["band"]["end"] + 1)
    text = probe_source()
    spelled = sorted(str(number) for number in band if str(number) in text)
    assert spelled == [], (
        "the port allocation record is the single owner of these numbers; the "
        f"probe restated {spelled}"
    )


def test_the_probe_source_measures_deadlines_on_a_monotonic_clock() -> None:
    assert "time.time" not in probe_source(), (
        "wall time is not monotonic, and an NTP step backwards silently extends "
        "a deadline built on it"
    )


def test_the_required_nodes_are_the_ones_the_page_script_asks_for() -> None:
    script = (config.default_web_dir() / "app.js").read_text(encoding="utf-8")
    unasked = [node for node in probe_module.REQUIRED_NODE_IDS if f'"{node}"' not in script]
    assert unasked == [], (
        f"every required id must be one app.js reaches for by name; these are not: {unasked}"
    )


def test_the_required_nodes_are_all_declared_by_the_page_it_grades() -> None:
    page = (config.default_web_dir() / "index.html").read_text(encoding="utf-8")
    declared = probe_module.document_ids(page)
    missing = [node for node in probe_module.REQUIRED_NODE_IDS if node not in declared]
    assert missing == []


def test_the_value_shape_renderer_never_reproduces_string_content() -> None:
    personal = "an account name or a world name would sit here"
    assert personal not in probe_module.value_shape(personal)


def test_the_help_text_says_the_screenshot_can_degrade() -> None:
    with pytest.raises(SystemExit) as raised:
        probe_module.parse_args(["--help"])
    said = (raised.value.code, "unavailable" in probe_module.EPILOG)
    assert said == (0, True)
