"""CS-1171 - the BEHAVIOURAL twin of every endpoint ``opens no file`` static arm.

``tests/surface/test_health.py``, ``test_map.py``, ``test_world.py`` and
``test_registry.py`` each carry a static arm that parses the endpoint module and
asserts it names no opener. That arm reads SOURCE, so it is defeated by two
edits it cannot see: an opener reached through a helper in ANOTHER module, and
an opener reached through a runtime-built name such as
``getattr(builtins, "op" + "en")``. Both were planted against a scratch copy
before this module was written, and the static arms stayed green under both.

This module drives each endpoint's real handler with the file-opening surface
instrumented, and fails naming the endpoint when anything is opened DURING THE
REQUEST. Two independent recorders are armed for the request call only:

a. WRAPPERS over ``builtins.open``, ``io.open``, ``os.open`` and
   ``pathlib.Path.open`` / ``read_text`` / ``read_bytes``. These name the
   channel an open went through.
b. AN AUDIT HOOK on the ``open`` event, which CPython raises from the C
   implementation of every one of those, so a reference to the opener captured
   before the wrappers were installed (``_io.open``) is still seen.

THE RECORDING IS SCOPED TO ONE HANDLER CALL ON ONE THREAD. The handler is
called once UNRECORDED first, so a lazy import the request path performs the
first time it runs - which reads a module file - is spent before recording
starts rather than read as the endpoint opening a file.

THE RECORDER IS PROVED LIVE BY A POSITIVE CONTROL PER ENDPOINT PER CHANNEL: a
provider that opens a file when the handler asks it for its value, which is an
open made from inside the request path. A recorder that sees nothing would pass
every twin below for that reason alone.

NO PATH IS RECORDED. The recorders keep only the fixed channel name, so a
failure report names the endpoint and the channel and never renders a file
path - a path under a home directory is exactly what non-negotiable 12 forbids
echoing.
"""

from __future__ import annotations

import _io
import builtins
import contextlib
import io
import os
import pathlib
import sys
import threading
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.surface.api import health, registry, world
from clockspeed.surface.api import map as map_endpoint
from tests.solve import synthetic as solve_synthetic
from tests.surface import test_map as map_fixtures
from tests.surface import test_world as world_fixtures

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from clockspeed.surface.api import contract

#: The endpoints whose static arm this module twins. Asserted before any sweep.
EXPECTED_ENDPOINTS: Final = 4

#: The channels the positive control opens through. Asserted before any sweep.
EXPECTED_CONTROLS: Final = 5

#: The file every control opens: this module's own source, read-only, tracked,
#: and carrying nothing personal.
_OWN_SOURCE: Final = pathlib.Path(__file__)

#: The audit event CPython raises for every file open.
_AUDIT_OPEN: Final = "open"


# ---------------------------------------------------------------------------
# The recorder
# ---------------------------------------------------------------------------


class _Recorder:
    """Holds whether recording is armed, on which thread, and what it saw."""

    def __init__(self) -> None:
        """Start disarmed with nothing seen."""
        self.armed = False
        self.thread: int | None = None
        self.seen: list[str] = []

    def note(self, channel: str) -> None:
        """Record one open, if armed and on the armed thread.

        Args:
            channel: The fixed channel name. Never a path.
        """
        if self.armed and threading.get_ident() == self.thread:
            self.seen.append(channel)


_RECORDER: Final = _Recorder()


def _audit(event: str, _args: tuple[object, ...]) -> None:
    """The audit hook. Records the event name only, never its arguments.

    Args:
        event: The audit event name.
        _args: The event arguments, which carry the path and are not kept.
    """
    if event == _AUDIT_OPEN:
        _RECORDER.note("audit:open")


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
    """Arm both recorders for the body of the block, on this thread only.

    Yields:
        The live list of channel names seen while armed.
    """
    saved = [(owner, name, getattr(owner, name)) for owner, name, _ in _PATCHED]
    for (owner, name, channel), (_, _, original) in zip(_PATCHED, saved, strict=True):
        setattr(owner, name, _wrap(channel, original))
    _RECORDER.seen = []
    _RECORDER.thread = threading.get_ident()
    _RECORDER.armed = True
    try:
        yield _RECORDER.seen
    finally:
        _RECORDER.armed = False
        _RECORDER.thread = None
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


def _health(side_effect: Callable[[], None]) -> contract.Handler:
    held = _Held(object(), object(), side_effect)
    return health.make_handler(held, held, {})


def _map(side_effect: Callable[[], None]) -> contract.Handler:
    extractor = map_fixtures.miner_extractor()
    held = _Held(
        map_fixtures.canary_world(),
        map_fixtures.fixture_registry(extractor=extractor),
        side_effect,
    )
    return map_endpoint.make_handler(held, held)  # type: ignore[arg-type]


def _world(side_effect: Callable[[], None]) -> contract.Handler:
    held = _Held(world_fixtures.canary_world(), None, side_effect)
    return world.make_handler(held)  # type: ignore[arg-type]


def _registry(side_effect: Callable[[], None]) -> contract.Handler:
    held = _Held(None, solve_synthetic.solve_registry(), side_effect)
    return registry.make_handler(held)  # type: ignore[arg-type]


#: Each endpoint's name and the builder of its real handler.
_ENDPOINTS: Final[tuple[tuple[str, Callable[[Callable[[], None]], contract.Handler]], ...]] = (
    (health.ENDPOINT, _health),
    (map_endpoint.ENDPOINT, _map),
    (world.ENDPOINT, _world),
    (registry.ENDPOINT, _registry),
)


def _open_builtin() -> None:
    with open(_OWN_SOURCE, "rb"):  # noqa: PTH123 - the builtin IS the channel under test
        pass


def _open_os() -> None:
    os.close(os.open(_OWN_SOURCE, os.O_RDONLY))


def _open_read_text() -> None:
    _OWN_SOURCE.read_text(encoding="ascii")


def _open_runtime_name() -> None:
    opener = getattr(builtins, "op" + "en")
    with opener(_OWN_SOURCE, "rb"):
        pass


def _open_captured() -> None:
    # A reference to the C opener that no wrapper replaces - only the audit
    # hook can see an open made through it.
    with _io.open(_OWN_SOURCE, "rb"):
        pass


#: Each control's name, its opener, and the channel that MUST see it.
_CONTROLS: Final = (
    ("builtin", _open_builtin, "builtins.open"),
    ("os", _open_os, "os.open"),
    ("read_text", _open_read_text, "Path.read_text"),
    ("runtime_name", _open_runtime_name, "builtins.open"),
    ("captured", _open_captured, "audit:open"),
)


def _drive(
    build: Callable[[Callable[[], None]], contract.Handler], side_effect: Callable[[], None]
) -> list[str]:
    """Build the handler, warm it once unrecorded, then record one request.

    Args:
        build: The endpoint's handler builder.
        side_effect: What the provider runs on every question.

    Returns:
        The channel names seen during the recorded request.
    """
    handler = build(side_effect)
    handler({})
    with _recording() as seen:
        handler({})
    return list(seen)


# ---------------------------------------------------------------------------
# The arms
# ---------------------------------------------------------------------------


def test_the_populations_are_the_sizes_this_module_claims() -> None:
    """A sweep over an empty population is green and grades nothing."""
    endpoints = len(_ENDPOINTS)
    assert endpoints == EXPECTED_ENDPOINTS, endpoints
    controls = len(_CONTROLS)
    assert controls == EXPECTED_CONTROLS, controls
    distinct = len({name for name, _ in _ENDPOINTS})
    assert distinct == EXPECTED_ENDPOINTS, distinct


@pytest.mark.parametrize(("name", "build"), _ENDPOINTS, ids=[name for name, _ in _ENDPOINTS])
def test_the_endpoint_opens_no_file_during_a_request(
    name: str, build: Callable[[Callable[[], None]], contract.Handler]
) -> None:
    """The twin. Nothing is opened, through any channel, while the request runs."""
    seen = _drive(build, _no_open)
    opened = len(seen)
    channels = str(sorted(set(seen)))
    assert opened == 0, name + " opened a file during the request via " + channels


@pytest.mark.parametrize(("name", "build"), _ENDPOINTS, ids=[name for name, _ in _ENDPOINTS])
@pytest.mark.parametrize(
    ("control", "opener", "channel"), _CONTROLS, ids=[control for control, _, _ in _CONTROLS]
)
def test_the_recorder_sees_an_open_made_from_inside_the_request(
    name: str,
    build: Callable[[Callable[[], None]], contract.Handler],
    control: str,
    opener: Callable[[], None],
    channel: str,
) -> None:
    """The positive control. A provider the handler asks opens a file."""
    seen = _drive(build, opener)
    through_channel = seen.count(channel)
    through_audit = seen.count("audit:open")
    assert through_channel > 0, name + " / " + control + ": the channel recorder saw nothing"
    assert through_audit > 0, name + " / " + control + ": the audit recorder saw nothing"


def test_the_recorder_is_disarmed_outside_the_block() -> None:
    """An open after the block is not recorded, and every opener is restored."""
    with _recording() as seen:
        pass
    _open_builtin()
    after = len(seen)
    assert after == 0, after
    restored = sum(1 for owner, name, _ in _PATCHED if getattr(owner, name).__name__ == "wrapper")
    assert restored == 0, restored
