"""CS-1171 - the BEHAVIOURAL twin of every endpoint ``opens no file`` static arm.

``tests/surface/test_health.py``, ``test_map.py``, ``test_world.py`` and
``test_registry.py`` each carry a static arm that parses the endpoint module and
asserts it names no opener. That arm reads SOURCE, so it is defeated by two
edits it cannot see: an opener reached through a helper in ANOTHER module, and
an opener reached through a runtime-built name such as
``getattr(builtins, "op" + "en")``. Both were planted against a scratch copy
before this module was written, and the static arms stayed green under both.

This module drives each endpoint through the SAME route table and matcher the
real server dispatches with - ``routes.build_routes``, ``server.routing`` and
``server.match_route`` - with the file-opening surface instrumented, and fails
naming the endpoint when anything is opened DURING THE REQUEST. Two independent
recorders are armed for the request calls only:

a. WRAPPERS over ``builtins.open``, ``io.open``, ``os.open`` and
   ``pathlib.Path.open`` / ``read_text`` / ``read_bytes``. These name the
   channel an open went through.
b. AN AUDIT HOOK on every file-reaching audit event in :data:`_FILE_EVENTS` -
   ``open`` (raised from C by every opener above, ``io.FileIO``,
   ``io.open_code`` and a loader's ``get_data``), ``sqlite3.connect``,
   ``mmap.__new__``, the ``tempfile`` and ``shutil`` events, the Windows
   ``_winapi.CreateFile`` event, and the ``ctypes`` foreign-call events. The
   last are recorded because a direct ``CreateFileW`` through ``ctypes``
   raises no ``open`` event at all; recording EVERY foreign call is
   deliberately wider than "opens a file", and the pristine arms show no
   endpoint makes one.

THE RECORDING IS ARMED ON EVERY THREAD. An endpoint that starts a thread which
opens a file, and joins it, opened a file during the request.

THE FIRST CALL IS RECORDED. There is no unrecorded warm-up, so an endpoint that
opens a file only once and caches the result is caught on the call that did
it. The one exclusion is the import machinery reading a module's own source,
bytecode or extension file: an ``open`` event reached from ``_find_and_load``
through frozen import frames ONLY. The decision is made in the hook from the
call stack and never from the path, which is not kept. The walk outward from
the opener stops at the first frame that is not frozen import code and records
the open, so a direct ``loader.get_data(...)`` call from the request path is
recorded, and so is a data read made by an imported module's OWN top-level
code - ``__loader__.get_data``, ``pkgutil.get_data``, a plain ``open`` - because
that module's frame lies between the opener and ``_find_and_load``. An arm per
endpoint per variant proves each.

THE RECORDER IS PROVED LIVE BY A POSITIVE CONTROL PER ENDPOINT PER CHANNEL: a
provider that opens a file when the handler asks it for its value, which is an
open made from inside the request path. A recorder that sees nothing would pass
every twin below for that reason alone. A NEGATIVE control performs a fresh
import during the first recorded call and asserts it is NOT recorded, so the
import exclusion is shown to be what keeps the pristine arms green.

NAMED RESIDUAL. A foreign call that opens a file through a library already
loaded and a function pointer already resolved raises ``ctypes.call_function``,
which is recorded; a C extension module that opens a file in its own C code
raises no audit event at all and is invisible to this module by construction.
A thread the request STARTS BUT DOES NOT JOIN may open a file after the
recording window closes, and that open is not recorded: the window ends when
the handler returns, not when every thread it spawned has finished.

NO PATH IS RECORDED. The recorders keep only the fixed channel name, so a
failure report names the endpoint and the channel and never renders a file
path - a path under a home directory is exactly what non-negotiable 12 forbids
echoing.
"""

from __future__ import annotations

import _io
import builtins
import contextlib
import ctypes
import importlib
import io
import os
import pathlib
import sqlite3
import sys
import threading
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.surface import server
from clockspeed.surface.api import contract, health, registry, routes, world
from clockspeed.surface.api import map as map_endpoint
from tests.solve import synthetic as solve_synthetic
from tests.surface import test_map as map_fixtures
from tests.surface import test_world as world_fixtures

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from types import FrameType

#: The endpoints whose static arm this module twins. Asserted before any sweep.
EXPECTED_ENDPOINTS: Final = 4

#: The positive controls. Asserted before any sweep.
EXPECTED_CONTROLS: Final = 11

#: How many recorded requests each drive makes: the first call and a second.
RECORDED_CALLS: Final = 2

#: The file every control opens: this module's own source, read-only, tracked,
#: and carrying nothing personal.
_OWN_SOURCE: Final = pathlib.Path(__file__)

#: Every audit event that reaches a file, or that runs foreign code which could.
_FILE_EVENTS: Final = frozenset(
    {
        "open",
        "sqlite3.connect",
        "sqlite3.connect/handle",
        "mmap.__new__",
        "tempfile.mkstemp",
        "tempfile.mkdtemp",
        "shutil.copyfile",
        "shutil.copymode",
        "shutil.copystat",
        "shutil.copytree",
        "shutil.move",
        "shutil.rmtree",
        "shutil.make_archive",
        "shutil.unpack_archive",
        "_winapi.CreateFile",
        "_winapi.CreateNamedPipe",
        "msvcrt.open_osfhandle",
        "ctypes.dlopen",
        "ctypes.dlsym",
        "ctypes.call_function",
    }
)

#: The code objects the import machinery runs from.
_FROZEN_IMPORT: Final = frozenset(
    {
        "<frozen importlib._bootstrap>",
        "<frozen importlib._bootstrap_external>",
        "<frozen zipimport>",
    }
)

#: The frame that marks an import in flight.
_IMPORT_IN_FLIGHT: Final = "_find_and_load"


# ---------------------------------------------------------------------------
# The recorder
# ---------------------------------------------------------------------------


class _Recorder:
    """Holds whether recording is armed and what it saw, across every thread."""

    def __init__(self) -> None:
        """Start disarmed with nothing seen."""
        self.armed = False
        self.seen: list[str] = []
        self.lock = threading.Lock()

    def note(self, channel: str) -> None:
        """Record one open, if armed, from whichever thread made it.

        Args:
            channel: The fixed channel name. Never a path.
        """
        if self.armed:
            with self.lock:
                self.seen.append(channel)


_RECORDER: Final = _Recorder()


def _import_machinery_open() -> bool:
    """Whether the open being audited is the import system loading a module.

    Decided from the call stack alone. Frame 0 is this function and frame 1 the
    hook; frame 2 is the Python frame that called the C opener.

    THE WALK STOPS AT THE FIRST FRAME THAT IS NOT IMPORT MACHINERY. Every frame
    from the opener's caller outward to ``_find_and_load`` must be frozen import
    code. A module's own top-level code sits between the two whenever it reads
    a data file while being imported - through ``__loader__.get_data``,
    ``pkgutil.get_data`` or ``importlib.resources`` - and that frame is not
    frozen, so the read is recorded rather than mistaken for the loader reading
    the module's source.

    Returns:
        True only when an unbroken run of frozen import frames links the
        opener to ``_find_and_load``.
    """
    frame: FrameType | None = sys._getframe(2)  # noqa: SLF001 - the stack is the only non-path evidence
    while frame is not None:
        code = frame.f_code
        if code.co_filename not in _FROZEN_IMPORT:
            return False
        if code.co_name == _IMPORT_IN_FLIGHT:
            return True
        frame = frame.f_back
    return False


def _audit(event: str, _args: tuple[object, ...]) -> None:
    """The audit hook. Records the event name only, never its arguments.

    Args:
        event: The audit event name.
        _args: The event arguments, which carry the path and are not kept.
    """
    if not _RECORDER.armed or event not in _FILE_EVENTS:
        return
    if event == "open" and _import_machinery_open():
        return
    _RECORDER.note("audit:" + event)


# An audit hook cannot be removed, so it is installed once per process and
# does nothing unless the recorder is armed.
sys.addaudithook(_audit)


def _wrap(channel: str, original: Callable[..., object]) -> Callable[..., object]:
    """Wrap one opener so a call through it is recorded, then delegated.

    Args:
        channel: The fixed channel name.
        original: The opener being wrapped.

    Returns:
        The wrapper.
    """

    def wrapper(*args: object, **kwargs: object) -> object:
        _RECORDER.note(channel)
        return original(*args, **kwargs)

    return wrapper


#: Every patched attribute: (owner, attribute name, channel name).
_PATCHED: Final = (
    (builtins, "open", "builtins.open"),
    (io, "open", "io.open"),
    (os, "open", "os.open"),
    (pathlib.Path, "open", "Path.open"),
    (pathlib.Path, "read_text", "Path.read_text"),
    (pathlib.Path, "read_bytes", "Path.read_bytes"),
)


@contextlib.contextmanager
def _recording() -> Iterator[list[str]]:
    """Arm both recorders for the body of the block, on every thread.

    Yields:
        The live list of channel names seen while armed.
    """
    saved = [(owner, name, getattr(owner, name)) for owner, name, _ in _PATCHED]
    for (owner, name, channel), (_, _, original) in zip(_PATCHED, saved, strict=True):
        setattr(owner, name, _wrap(channel, original))
    _RECORDER.seen = []
    _RECORDER.armed = True
    try:
        yield _RECORDER.seen
    finally:
        _RECORDER.armed = False
        for owner, name, original in saved:
            setattr(owner, name, original)


# ---------------------------------------------------------------------------
# Providers and drivers
# ---------------------------------------------------------------------------


def _no_open() -> None:
    """The pristine provider side effect: nothing."""


class _Held:
    """A world AND registry provider that answers with one held value each.

    It runs ``side_effect`` every time it is asked, which is how the positive
    control makes an open from inside the request path.
    """

    def __init__(
        self,
        world_value: object,
        registry_value: object,
        side_effect: Callable[[], None] = _no_open,
    ) -> None:
        """Hold the answers and the side effect.

        Args:
            world_value: What ``world()`` returns.
            registry_value: What ``registry()`` returns.
            side_effect: What runs on every question.
        """
        self._world = world_value
        self._registry = registry_value
        self._side_effect = side_effect

    def world(self) -> object:
        """Run the side effect, then answer with the held world.

        Returns:
            The held world.
        """
        self._side_effect()
        return self._world

    def registry(self) -> object:
        """Run the side effect, then answer with the held registry.

        Returns:
            The held registry.
        """
        self._side_effect()
        return self._registry


def _health_inputs() -> tuple[object, object]:
    return world_fixtures.canary_world(), solve_synthetic.solve_registry()


def _map_inputs() -> tuple[object, object]:
    extractor = map_fixtures.miner_extractor()
    return map_fixtures.canary_world(), map_fixtures.fixture_registry(extractor=extractor)


def _world_inputs() -> tuple[object, object]:
    return world_fixtures.canary_world(), None


def _registry_inputs() -> tuple[object, object]:
    return None, solve_synthetic.solve_registry()


#: Each endpoint's template and the builder of what its providers hold.
_ENDPOINTS: Final[tuple[tuple[str, Callable[[], tuple[object, object]]], ...]] = (
    (health.ENDPOINT, _health_inputs),
    (map_endpoint.ENDPOINT, _map_inputs),
    (world.ENDPOINT, _world_inputs),
    (registry.ENDPOINT, _registry_inputs),
)


def _handler_for(
    template: str, inputs: Callable[[], tuple[object, object]], side_effect: Callable[[], None]
) -> tuple[contract.Handler, dict[str, str]]:
    """Resolve an endpoint's handler through the table the real server builds.

    Args:
        template: The endpoint template, used as the request path.
        inputs: The builder of what the providers hold.
        side_effect: What the providers run on every question.

    Returns:
        The GET handler the server would dispatch to, and the path captures.
    """
    world_value, registry_value = inputs()
    held = _Held(world_value, registry_value, side_effect)
    table = server.routing(routes.build_routes(held, held))  # type: ignore[arg-type]
    matched = server.match_route(table, template)
    assert matched is not None, template + " is not in the server's table"
    resolved, captured = matched
    assert resolved == template, template
    return table[resolved]["GET"], captured


def _drive(
    template: str, inputs: Callable[[], tuple[object, object]], side_effect: Callable[[], None]
) -> tuple[list[str], list[int]]:
    """Resolve the handler, then record its FIRST call and a second one.

    Args:
        template: The endpoint template.
        inputs: The builder of what the providers hold.
        side_effect: What the providers run on every question.

    Returns:
        The channel names seen, and the status of each recorded response.
    """
    handler, captured = _handler_for(template, inputs, side_effect)
    with _recording() as seen:
        statuses = [handler(dict(captured)).http_status for _ in range(RECORDED_CALLS)]
    return list(seen), statuses


# ---------------------------------------------------------------------------
# The positive controls - each returns a fresh side effect
# ---------------------------------------------------------------------------


def _open_builtin() -> None:
    with open(_OWN_SOURCE, "rb"):  # noqa: PTH123 - the builtin IS the channel under test
        pass


def _builtin() -> Callable[[], None]:
    return _open_builtin


def _os() -> Callable[[], None]:
    return lambda: os.close(os.open(_OWN_SOURCE, os.O_RDONLY))


def _read_text() -> Callable[[], None]:
    def effect() -> None:
        _OWN_SOURCE.read_text(encoding="ascii")

    return effect


def _runtime_name() -> Callable[[], None]:
    def effect() -> None:
        opener = getattr(builtins, "op" + "en")
        with opener(_OWN_SOURCE, "rb"):
            pass

    return effect


def _captured() -> Callable[[], None]:
    # A reference to the C opener that no wrapper replaces - only the audit
    # hook can see an open made through it.
    def effect() -> None:
        with _io.open(_OWN_SOURCE, "rb"):
            pass

    return effect


def _file_io() -> Callable[[], None]:
    return lambda: io.FileIO(_OWN_SOURCE).close()


def _loader_get_data() -> Callable[[], None]:
    # A loader read made directly, NOT under an import - the import exclusion
    # must not swallow it even though its immediate caller is frozen code.
    def effect() -> None:
        loader = health.__spec__.loader if health.__spec__ is not None else None
        assert loader is not None
        loader.get_data(health.__file__)  # type: ignore[attr-defined]

    return effect


def _thread() -> Callable[[], None]:
    def effect() -> None:
        worker = threading.Thread(target=_open_builtin)
        worker.start()
        worker.join()

    return effect


def _first_call_only() -> Callable[[], None]:
    done: list[bool] = []

    def effect() -> None:
        if not done:
            done.append(True)
            _open_builtin()

    return effect


def _sqlite() -> Callable[[], None]:
    def effect() -> None:
        uri = _OWN_SOURCE.as_uri() + "?mode=ro"
        with contextlib.suppress(sqlite3.Error):
            sqlite3.connect(uri, uri=True).close()

    return effect


def _foreign_call() -> Callable[[], None]:
    return lambda: ctypes.pythonapi.Py_IsInitialized() and None


#: Each control's name, its factory, and the channels that MUST each see it.
_CONTROLS: Final[tuple[tuple[str, Callable[[], Callable[[], None]], tuple[str, ...]], ...]] = (
    ("builtin", _builtin, ("builtins.open", "audit:open")),
    ("os", _os, ("os.open", "audit:open")),
    ("read_text", _read_text, ("Path.read_text", "audit:open")),
    ("runtime_name", _runtime_name, ("builtins.open", "audit:open")),
    ("captured", _captured, ("audit:open",)),
    ("file_io", _file_io, ("audit:open",)),
    ("loader_get_data", _loader_get_data, ("audit:open",)),
    ("thread", _thread, ("builtins.open", "audit:open")),
    ("first_call_only", _first_call_only, ("builtins.open", "audit:open")),
    ("sqlite", _sqlite, ("audit:sqlite3.connect",)),
    ("foreign_call", _foreign_call, ("audit:ctypes.call_function",)),
)

#: A pure stdlib module this module never imports, re-imported fresh by the
#: negative control.
_FRESH_IMPORT: Final = "colorsys"


# ---------------------------------------------------------------------------
# The arms
# ---------------------------------------------------------------------------


_ENDPOINT_IDS: Final = [template for template, _ in _ENDPOINTS]


def test_the_populations_are_the_sizes_this_module_claims() -> None:
    """A sweep over an empty population is green and grades nothing."""
    endpoints = len(_ENDPOINTS)
    assert endpoints == EXPECTED_ENDPOINTS, endpoints
    controls = len(_CONTROLS)
    assert controls == EXPECTED_CONTROLS, controls
    distinct = len(set(_ENDPOINT_IDS))
    assert distinct == EXPECTED_ENDPOINTS, distinct


@pytest.mark.parametrize(("template", "inputs"), _ENDPOINTS, ids=_ENDPOINT_IDS)
def test_the_endpoint_opens_no_file_during_a_request(
    template: str, inputs: Callable[[], tuple[object, object]]
) -> None:
    """The twin. Nothing is opened, on any thread, on the first call or after."""
    seen, statuses = _drive(template, inputs, _no_open)
    answered = statuses.count(contract.HTTP_OK)
    assert answered == RECORDED_CALLS, template + " did not answer 200 on every call"
    opened = len(seen)
    channels = str(sorted(set(seen)))
    assert opened == 0, template + " opened a file during the request via " + channels


@pytest.mark.parametrize(("template", "inputs"), _ENDPOINTS, ids=_ENDPOINT_IDS)
@pytest.mark.parametrize(
    ("control", "factory", "channels"), _CONTROLS, ids=[control for control, _, _ in _CONTROLS]
)
def test_the_recorder_sees_an_open_made_from_inside_the_request(
    template: str,
    inputs: Callable[[], tuple[object, object]],
    control: str,
    factory: Callable[[], Callable[[], None]],
    channels: tuple[str, ...],
) -> None:
    """The positive control. A provider the handler asks opens a file."""
    seen, _statuses = _drive(template, inputs, factory())
    blind = [channel for channel in channels if seen.count(channel) == 0]
    missed = len(blind)
    assert missed == 0, template + " / " + control + ": blind recorder(s) " + str(blind)


@pytest.mark.parametrize(("template", "inputs"), _ENDPOINTS, ids=_ENDPOINT_IDS)
def test_a_fresh_import_on_the_first_call_is_not_read_as_an_open(
    template: str, inputs: Callable[[], tuple[object, object]]
) -> None:
    """The negative control. The import machinery's own reads are excluded."""
    imported: list[bool] = []

    def effect() -> None:
        if not imported:
            imported.append(True)
            sys.modules.pop(_FRESH_IMPORT, None)
            importlib.import_module(_FRESH_IMPORT)

    seen, _statuses = _drive(template, inputs, effect)
    ran = len(imported)
    assert ran == 1, ran
    opened = len(seen)
    assert opened == 0, template + ": an import was read as an open via " + str(sorted(set(seen)))


#: Top-level bodies of a module imported DURING the request, each of which
#: reads a data file through a loader - and so has frozen loader code as the
#: opener's immediate caller while ``_find_and_load`` is on the stack.
_TOP_LEVEL_READS: Final = (
    ("loader_get_data", "_D = __loader__.get_data(__file__)\n", "__import__"),
    (
        "pkgutil_get_data",
        "import os\nimport pkgutil\n_D = pkgutil.get_data(__name__, os.path.basename(__file__))\n",
        "__import__",
    ),
    ("import_module", "_D = __loader__.get_data(__file__)\n", "import_module"),
)

#: How many top-level read variants the arm below sweeps.
EXPECTED_TOP_LEVEL_READS: Final = 3


def test_the_top_level_read_population_is_the_size_it_claims() -> None:
    """A sweep over an empty population is green and grades nothing."""
    variants = len(_TOP_LEVEL_READS)
    assert variants == EXPECTED_TOP_LEVEL_READS, variants


@pytest.mark.parametrize(("template", "inputs"), _ENDPOINTS, ids=_ENDPOINT_IDS)
@pytest.mark.parametrize(
    ("variant", "body", "how"),
    _TOP_LEVEL_READS,
    ids=[variant for variant, _, _ in _TOP_LEVEL_READS],
)
def test_a_data_read_by_an_imported_module_s_top_level_code_is_recorded(
    template: str,
    inputs: Callable[[], tuple[object, object]],
    variant: str,
    body: str,
    how: str,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The import exclusion must not swallow a data read made while importing.

    The module is written BEFORE recording starts, so the only opens inside the
    window are the import machinery reading its source - excluded - and the
    module's own top-level read - which must be recorded.
    """
    name = "cs1171_top_level_" + variant
    (tmp_path / (name + ".py")).write_bytes(body.encode("ascii"))
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    sys.modules.pop(name, None)

    def effect() -> None:
        if name in sys.modules:
            return
        if how == "import_module":
            importlib.import_module(name)
        else:
            __import__(name)

    try:
        seen, _statuses = _drive(template, inputs, effect)
    finally:
        sys.modules.pop(name, None)
    recorded = seen.count("audit:open")
    assert recorded > 0, template + " / " + variant + ": a top-level data read was excluded"


def test_the_fresh_import_really_reads_a_file_when_not_excluded() -> None:
    """The exclusion is not vacuous: the same import DOES raise an open event."""
    events: list[str] = []

    def spy(event: str, _args: tuple[object, ...]) -> None:
        if event == "open" and armed:
            events.append(event)

    armed = False
    sys.addaudithook(spy)
    sys.modules.pop(_FRESH_IMPORT, None)
    armed = True
    importlib.import_module(_FRESH_IMPORT)
    armed = False
    raised = len(events)
    assert raised > 0, raised


def test_the_recorder_is_disarmed_outside_the_block() -> None:
    """An open after the block is not recorded, and every opener is restored."""
    with _recording() as seen:
        pass
    _open_builtin()
    after = len(seen)
    assert after == 0, after
    left = sum(1 for owner, name, _ in _PATCHED if getattr(owner, name).__name__ == "wrapper")
    assert left == 0, left
