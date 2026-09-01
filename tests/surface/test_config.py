"""CS-601 slice S2 - where the dashboard listens, and what it listens with.

What is covered, and the authority for each arm:

a. THE PORT HAS EXACTLY ONE OWNER AND IT IS NOT THIS TREE.
   ``clockspeed/surface/__init__.py``: "The port is ALLOCATED, recorded once in
   the project configuration, and read from there. It is not restated in code
   (CONVENTIONS.md section 2)." So no arm below spells the number, and one arm
   sweeps this whole test package for an integer literal anywhere in the
   allocated band - the band itself read from the record, never typed here.
   That arm is what stops a later test pinning the number a second time and
   turning the record into a decoration.
b. PRECEDENCE IS STATED, NOT ASSUMED. ``--port`` beats the environment beats the
   record. Each step is asserted against the step below it rather than against a
   literal, so the arms stay true when the allocation moves - and it MOVED this
   session, which is exactly the event that would have falsified a literal.
c. A ``ServerConfig`` HOLDS THREE ``Path`` FIELDS AND MUST NOT RENDER THEM.
   ``tests/repr_rendering_guard.py`` grades that statically under R2; the arm
   here is the runtime companion, planting a canary inside every path and
   asserting the rendered repr carries it zero times. The detector is then run
   against a deliberately leaky repr, so "found nothing" is distinguishable from
   "looks for nothing" (CONVENTIONS.md section 7.2).
d. THE CERTIFICATE PAIR IS NAMED IN TWO FILES AND THEY MUST AGREE.
   ``scripts/make_cert.py`` WRITES the pair and this module READS it. That is a
   restated fact and therefore a fact that will drift (CLAUDE.md section 4), so
   one arm parses the script's own literals out of its AST and asserts the two
   spellings are identical. The duplication is a reported seam collision; this
   arm is what keeps it honest until the ownership is moved.
e. A BROKEN RECORD IS A FIXED LINE, NEVER AN ECHO. The record path can sit under
   a home directory, so a refusal is asserted to carry neither the path nor any
   fragment of the file it refused (non-negotiable 3).
f. AND SO IS THE CAUSE THAT REFUSAL IS CHAINED TO. CS-857. Arm (e) reads
   ``str()`` on the ConfigError and nothing else, and that is the whole of what
   it can see: ``raise X from exc`` makes the CAUSE's own text part of the
   formatted traceback, and ``OSError.__str__`` appends ``filename``. A wrapper
   hardened by construction therefore still handed the record path to the
   renderer above it. Two arms grade the repair, because neither is sufficient
   alone - one reads the DEFAULT EXCEPTHOOK's real output from a subprocess,
   which is the only place the ``__context__`` channel is visible at all, and
   one reads the cause's named fields, which is the only place "the reason
   survived" is visible. A third pins that the reason is genuinely still there,
   so a repair that closed the channel by dropping the cause turns this section
   red rather than green.

Test-quality discipline (CONVENTIONS.md section 7.2). Every sweep binds its
population size to a scalar and asserts the expected count BEFORE it iterates: a
sweep over an empty collection passes vacuously and proves nothing. Every
assertion about an absence is bound to a scalar too, because pytest renders the
asserted EXPRESSION independently of the message - asserting on the collection
itself is how this repository once shipped a path leak inside its own PII guard.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pytest

from clockspeed.data.locate import redact
from clockspeed.surface import config

# ---------------------------------------------------------------------------
# Populations, each with the count its sweep asserts before iterating
# ---------------------------------------------------------------------------

#: This test package. Swept for a port literal, so the number stays in one file.
TEST_PACKAGE: Final = Path(__file__).resolve().parent

#: Modules the port sweep expects to find. Asserted BEFORE the sweep iterates,
#: so a rename that empties the population turns the arm red instead of green.
MIN_SWEPT_TEST_MODULES: Final = 2

#: A string no path on any machine carries, planted into a path and then counted
#: in a rendering. Long and arbitrary, so a substring hit is a real hit.
CANARY: Final = "zqxjcanary601s2"

#: The minting script whose two filenames this module has to agree with.
MAKE_CERT: Final = "scripts/make_cert.py"

#: The names arm (d) lifts out of that script, mapped to this module's spelling.
CERT_LITERAL_PAIRS: Final = (
    ("CERT_NAME", "CERT_NAME"),
    ("KEY_NAME", "KEY_NAME"),
    ("ENV_CERT_DIR", "CERT_DIR_ENV"),
    ("DEFAULT_CERT_DIRNAME", "DEFAULT_CERT_DIRNAME"),
)

#: The transport's own range. Not an allocation, so it is not the record's to own.
LOWEST_PORT: Final = 0
HIGHEST_PORT: Final = 65535

#: Files that exist at the repository root and nowhere above it. Three rather
#: than one, because any single landmark could also sit in a parent directory.
ROOT_LANDMARKS: Final = ("pyproject.toml", "CLAUDE.md", "config/ports.json")


# ---------------------------------------------------------------------------
# Detectors. Each is used to prove an absence, so each is also run against a
# planted POSITIVE below - a detector that looks for nothing finds nothing.
# ---------------------------------------------------------------------------


def port_literals_in(source: str, low: int, high: int) -> list[int]:
    """Every integer literal in ``source`` that falls inside the closed band.

    Args:
        source: Python source text.
        low: The band's first port.
        high: The band's last port.

    Returns:
        The offending literals, in the order the parser met them.
    """
    return [
        node.value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
        and low <= node.value <= high
    ]


def canary_hits(rendering: str) -> int:
    """How many times the planted canary survives into a rendering.

    Args:
        rendering: Whatever the object rendered as.

    Returns:
        The occurrence count. Zero is the only passing answer for a real config.
    """
    return rendering.count(CANARY)


def module_literal(tree: ast.Module, name: str) -> str | None:
    """The string a module-level ``NAME = "..."`` assignment binds.

    Args:
        tree: A parsed module.
        name: The identifier to find.

    Returns:
        The bound string, or None when the module does not bind that name to
        a string constant at module level.
    """
    for node in tree.body:
        # THE NARROWING IS A STATEMENT AND NOT A TERNARY, so it reaches the read
        # below. An `isinstance` inside a conditional expression narrows only
        # inside that expression, so `node` was back to `ast.stmt` by the time
        # `node.value` was read - and `ast.stmt` genuinely HAS no `.value`. The
        # ternary was not merely unannotated; it was reading an attribute the
        # declared type does not carry, on a statement kind neither arm admits.
        if isinstance(node, ast.Assign):
            targets: tuple[ast.expr, ...] = tuple(node.targets)
        elif isinstance(node, ast.AnnAssign):
            targets = (node.target,)
        else:
            continue
        # `AnnAssign.value` is `expr | None`, and that None is a REAL module-level
        # shape rather than a typing artefact: `NAME: str` declares a name and
        # binds nothing. It leaves through the constant check, which is the one
        # place a value that is absent and a value that is not a string are
        # deliberately given the same answer - this helper reports what a module
        # BINDS, and both of those bind no string.
        bound = node.value
        if not isinstance(bound, ast.Constant) or not isinstance(bound.value, str):
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id == name:
                return bound.value
    return None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def band() -> tuple[int, int]:
    """The allocated band, read from the record rather than typed here.

    Returns:
        (first port, last port).
    """
    payload = json.loads(config.ports_record_path().read_text(encoding="ascii"))
    return int(payload["band"]["start"]), int(payload["band"]["end"])


@pytest.fixture
def synthetic_record(tmp_path: Path) -> Path:
    """A record whose base is deliberately NOT the allocated one.

    A test that used the real base could not tell "read the record" apart from
    "returned the number it was going to return anyway".

    ``band.start`` IS DELIBERATELY A DIFFERENT NUMBER FROM ``base``, and that is
    a repair rather than a detail. The real record happens to carry the same
    value under both keys, so while this fixture mirrored that, a mutation
    reading ``band.start`` instead of ``base`` passed all thirty arms - MEASURED,
    not supposed. Two keys that always agree are one key as far as any test can
    see, and the arm was proving nothing about which one was read. Keep these
    two numbers different.

    Returns:
        The written record.
    """
    path = tmp_path / "ports.json"
    payload = {"schema": 1, "base": 1234, "band": {"start": 1300, "end": 1400}}
    path.write_text(json.dumps(payload), encoding="ascii")
    return path


# ---------------------------------------------------------------------------
# (a) The port has exactly one owner
# ---------------------------------------------------------------------------


def test_the_allocated_port_is_the_records_base_and_is_not_spelled_in_code() -> None:
    record = config.ports_record_path()
    payload = json.loads(record.read_text(encoding="ascii"))
    assert config.allocated_port() == payload["base"]


def test_the_repo_root_is_the_directory_that_holds_the_record() -> None:
    root = config.repo_root()
    found = sum(1 for name in ROOT_LANDMARKS if (root / name).exists())
    assert found == len(ROOT_LANDMARKS)


def test_the_module_source_spells_no_port_in_the_allocated_band(band: tuple[int, int]) -> None:
    low, high = band
    source = Path(config.__file__).read_text(encoding="ascii")
    offenders = len(port_literals_in(source, low, high))
    assert offenders == 0, "clockspeed/surface/config.py restates an allocated port number"


def test_no_test_module_in_this_package_spells_a_port_in_the_allocated_band(
    band: tuple[int, int],
) -> None:
    low, high = band
    modules = sorted(TEST_PACKAGE.glob("test_*.py"))
    swept = len(modules)
    assert swept >= MIN_SWEPT_TEST_MODULES, "the port sweep found too few modules to be meaningful"
    offending_modules = sum(
        1 for path in modules if port_literals_in(path.read_text(encoding="ascii"), low, high)
    )
    assert offending_modules == 0, "a test in tests/surface/ pins an allocated port number"


def test_the_port_literal_detector_finds_a_planted_positive(band: tuple[int, int]) -> None:
    low, high = band
    planted = f"LISTEN_ON = {low}\n"
    found = len(port_literals_in(planted, low, high))
    assert found == 1


def test_the_port_literal_detector_ignores_a_number_outside_the_band(band: tuple[int, int]) -> None:
    low, high = band
    planted = f"OTHER = {low - 1}\nALSO = {high + 1}\n"
    found = len(port_literals_in(planted, low, high))
    assert found == 0


# ---------------------------------------------------------------------------
# (b) Precedence, each step asserted against the step below it
# ---------------------------------------------------------------------------


def test_the_record_is_the_answer_when_nothing_overrides(synthetic_record: Path) -> None:
    from_record = json.loads(synthetic_record.read_text(encoding="ascii"))["base"]
    assert config.resolve_port(env={}, record=synthetic_record) == from_record


def test_the_environment_beats_the_record(synthetic_record: Path) -> None:
    from_record = json.loads(synthetic_record.read_text(encoding="ascii"))["base"]
    declared = from_record + 1
    chosen = config.resolve_port(env={config.PORT_ENV: str(declared)}, record=synthetic_record)
    assert chosen == declared
    assert chosen != from_record


def test_a_requested_port_beats_both_the_environment_and_the_record(
    synthetic_record: Path,
) -> None:
    from_record = json.loads(synthetic_record.read_text(encoding="ascii"))["base"]
    from_env = from_record + 1
    requested = from_record + 2
    chosen = config.resolve_port(
        requested=requested,
        env={config.PORT_ENV: str(from_env)},
        record=synthetic_record,
    )
    assert chosen == requested
    assert chosen != from_env
    assert chosen != from_record


def test_port_zero_is_requestable_because_every_test_binds_it(synthetic_record: Path) -> None:
    assert config.resolve_port(requested=LOWEST_PORT, env={}, record=synthetic_record) == 0


def test_a_non_integer_environment_port_is_refused_rather_than_ignored(
    synthetic_record: Path,
) -> None:
    with pytest.raises(config.ConfigError) as caught:
        config.resolve_port(env={config.PORT_ENV: "not-a-number"}, record=synthetic_record)
    assert config.PORT_NOT_AN_INTEGER in str(caught.value)


def test_an_environment_port_outside_the_transport_range_is_refused(
    synthetic_record: Path,
) -> None:
    with pytest.raises(config.ConfigError) as caught:
        config.resolve_port(env={config.PORT_ENV: str(HIGHEST_PORT + 1)}, record=synthetic_record)
    assert config.PORT_OUT_OF_RANGE in str(caught.value)


def test_a_requested_port_outside_the_transport_range_is_refused(synthetic_record: Path) -> None:
    with pytest.raises(config.ConfigError) as caught:
        config.resolve_port(requested=-1, env={}, record=synthetic_record)
    assert config.PORT_OUT_OF_RANGE in str(caught.value)


# ---------------------------------------------------------------------------
# (e) A broken record is a fixed line, never an echo
# ---------------------------------------------------------------------------


def test_a_missing_record_refuses_with_a_fixed_line_that_does_not_echo_the_path(
    tmp_path: Path,
) -> None:
    missing = tmp_path / CANARY / "ports.json"
    with pytest.raises(config.ConfigError) as caught:
        config.allocated_port(missing)
    message = str(caught.value)
    assert config.RECORD_UNREADABLE in message
    leaked = canary_hits(message)
    assert leaked == 0, "the refusal echoed the path it refused"


def test_a_record_that_is_not_json_refuses_without_echoing_its_content(tmp_path: Path) -> None:
    path = tmp_path / "ports.json"
    path.write_text(f"this is not json and it mentions {CANARY}", encoding="ascii")
    with pytest.raises(config.ConfigError) as caught:
        config.allocated_port(path)
    message = str(caught.value)
    assert config.RECORD_MALFORMED in message
    leaked = canary_hits(message)
    assert leaked == 0, "the refusal echoed the file it refused"


def test_a_record_whose_base_is_not_an_integer_refuses(tmp_path: Path) -> None:
    path = tmp_path / "ports.json"
    path.write_text(json.dumps({"schema": 1, "base": CANARY}), encoding="ascii")
    with pytest.raises(config.ConfigError) as caught:
        config.allocated_port(path)
    message = str(caught.value)
    assert config.RECORD_MALFORMED in message
    leaked = canary_hits(message)
    assert leaked == 0


def test_a_record_with_no_base_at_all_refuses(tmp_path: Path) -> None:
    path = tmp_path / "ports.json"
    path.write_text(json.dumps({"schema": 1}), encoding="ascii")
    with pytest.raises(config.ConfigError):
        config.allocated_port(path)


# ---------------------------------------------------------------------------
# (c) A ServerConfig holds three Path fields and must not render them
# ---------------------------------------------------------------------------


def built_config(tmp_path: Path) -> config.ServerConfig:
    """A config whose every path carries the canary.

    Args:
        tmp_path: pytest's per-test directory.

    Returns:
        The config under test.
    """
    return config.ServerConfig(
        host=config.LOOPBACK,
        port=LOWEST_PORT,
        cert_path=tmp_path / CANARY / "dashboard.cert.pem",
        key_path=tmp_path / CANARY / "dashboard.key.pem",
        web_dir=tmp_path / CANARY / "web",
    )


def test_the_server_config_repr_withholds_every_path_it_holds(tmp_path: Path) -> None:
    leaked = canary_hits(repr(built_config(tmp_path)))
    assert leaked == 0, "ServerConfig.__repr__ rendered a path"


def test_the_server_config_str_withholds_every_path_it_holds(tmp_path: Path) -> None:
    leaked = canary_hits(str(built_config(tmp_path)))
    assert leaked == 0, "str(ServerConfig) rendered a path"


def test_the_server_config_repr_still_names_its_own_type(tmp_path: Path) -> None:
    assert "ServerConfig" in repr(built_config(tmp_path))


def test_the_canary_detector_finds_a_deliberately_leaky_repr(tmp_path: Path) -> None:
    @dataclass(frozen=True, repr=False)
    class Leaky:
        cert_path: Path

        def __repr__(self) -> str:
            return f"Leaky(cert_path={self.cert_path})"

    found = canary_hits(repr(Leaky(cert_path=tmp_path / CANARY / "x.pem")))
    assert found == 1, "the canary detector cannot see a leak, so its zeroes prove nothing"


def test_the_canary_detector_finds_a_generated_repr(tmp_path: Path) -> None:
    @dataclass(frozen=True)
    class Generated:
        cert_path: Path

    found = canary_hits(repr(Generated(cert_path=tmp_path / CANARY / "x.pem")))
    assert found == 1, "a generated repr is the exact leak R2 exists to catch"


def test_a_server_config_is_frozen(tmp_path: Path) -> None:
    built = built_config(tmp_path)
    with pytest.raises(AttributeError):
        built.port = HIGHEST_PORT  # type: ignore[misc]


# ---------------------------------------------------------------------------
# (d) The certificate pair is named in two files and they must agree
# ---------------------------------------------------------------------------


def test_the_certificate_pair_is_spelled_the_same_here_and_in_the_minting_script() -> None:
    script = config.repo_root() / MAKE_CERT
    assert script.is_file(), "the minting script moved; arm (d) is no longer checking anything"
    tree = ast.parse(script.read_text(encoding="ascii"))
    checked = 0
    disagreements = 0
    for script_name, config_name in CERT_LITERAL_PAIRS:
        theirs = module_literal(tree, script_name)
        ours = getattr(config, config_name, None)
        if theirs is None or ours is None:
            disagreements += 1
            continue
        checked += 1
        if theirs != ours:
            disagreements += 1
    assert checked == len(CERT_LITERAL_PAIRS), "a certificate literal is no longer readable"
    assert disagreements == 0, "the certificate pair drifted between config.py and make_cert.py"


def test_the_certificate_paths_sit_under_the_resolved_certificate_directory() -> None:
    built = config.load_config(requested_port=LOWEST_PORT, env={})
    # EVERY COMPARISON BELOW IS REDUCED TO A BOOL OR A BARE NAME FIRST. Writing
    # `assert built.cert_path.name == config.CERT_NAME` reads correctly and is
    # still a leak: pytest reprs the sub-expressions of a failing assert
    # independently of its message, so `built.cert_path` renders in full - the
    # certificate directory can sit under a home directory. Measured by
    # tests/test_assertion_rendering.py, which caught seven of these here.
    same_directory = built.cert_path.parent == built.key_path.parent
    cert_named_right = built.cert_path.name == config.CERT_NAME
    key_named_right = built.key_path.name == config.KEY_NAME
    assert same_directory is True
    assert cert_named_right is True, "the certificate is not the file make_cert.py writes"
    assert key_named_right is True, "the key is not the file make_cert.py writes"


def test_the_certificate_directory_honours_its_environment_override(tmp_path: Path) -> None:
    elsewhere = tmp_path / "elsewhere"
    built = config.load_config(
        requested_port=LOWEST_PORT, env={config.CERT_DIR_ENV: str(elsewhere)}
    )
    honoured = built.cert_path.parent == elsewhere
    assert honoured is True


# ---------------------------------------------------------------------------
# The rest of the config surface
# ---------------------------------------------------------------------------


def test_the_config_binds_loopback_and_never_a_wildcard() -> None:
    built = config.load_config(requested_port=LOWEST_PORT, env={})
    assert built.host == config.LOOPBACK
    assert built.host != "0.0.0.0"  # noqa: S104
    assert built.host != ""


def test_the_web_directory_sits_inside_the_surface_package() -> None:
    built = config.load_config(requested_port=LOWEST_PORT, env={})
    inside = built.web_dir.parent == Path(config.__file__).resolve().parent
    assert inside is True


def test_the_web_directory_is_not_required_to_exist() -> None:
    built = config.load_config(requested_port=LOWEST_PORT, env={})
    is_a_path = isinstance(built.web_dir, Path)
    assert is_a_path is True


def test_load_config_reads_the_real_record_when_nothing_overrides() -> None:
    built = config.load_config(env={})
    assert built.port == config.allocated_port()


# ---------------------------------------------------------------------------
# (f) CS-857 - the cause that refusal is chained to renders no path either
# ---------------------------------------------------------------------------

#: A digit run planted as a path segment and then looked for in a rendering.
#: Invented here and belonging to no machine, so non-negotiable 3 permits naming
#: it in an assertion message - which the tmp_path underneath it does not.
#:
#: IT IS THE NEEDLE PRECISELY BECAUSE redact() REWRITES IT, and every arm below
#: proves that rewrite before drawing any conclusion from the needle's absence. A
#: needle redact() does not touch is missing from a LEAKING rendering exactly as
#: reliably as from a clean one, so an unproven needle turns this section green
#: while measuring nothing. The rewrite comes from the digit-run backstop in
#: clockspeed/data/locate.py, which is machine-independent - unlike the home
#: prefix inside a tmp_path, which is only redactable on a runner whose temporary
#: directory happens to sit below one. CANARY cannot serve here for exactly that
#: reason: redact() leaves it untouched, so its absence would prove nothing.
RECORD_NEEDLE: Final = "10000000000000002"

#: How long the out-of-process arm may take before it is called hung. Bounded,
#: for the reason every other probe in this tree is bounded.
DRIVER_TIMEOUT_SECONDS: Final = 120

#: A one-shot program that drives :func:`allocated_port` and lets the failure
#: reach the DEFAULT EXCEPTHOOK - the renderer CS-857 is actually about. Passed
#: with ``-c`` so nothing is written to disk, and handed the repository root
#: explicitly rather than inheriting a working directory, so the arm does not
#: depend on where the suite was invoked from.
#:
#: THE EXCEPTHOOK RATHER THAN ``traceback.format_exception``, and that is not a
#: stylistic preference. Formatting a caught exception inside the test process
#: renders an absolute path per frame and ends in ``str(exc)``, which is the
#: channel ``tests/test_exception_rendering.py`` exists to keep out of this tree
#: - an arm proving that nothing leaks must not leak in order to prove it.
#: Letting a subprocess die is also the stronger evidence, because it measures
#: the real renderer instead of a stand-in for it.
RECORD_SITE_DRIVER: Final = (
    "import sys\n"
    "from pathlib import Path\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "from clockspeed.surface.config import allocated_port\n"
    "allocated_port(Path(sys.argv[2]))\n"
)


@dataclass(frozen=True)
class CauseFacts:
    """What the chained cause carries, reduced to booleans and nothing else.

    Attributes:
        is_oserror: The refusal is chained to an OSError at all.
        filename_cleared: ``filename`` is unset on it.
        filename2_cleared: ``filename2`` is unset on it.
        errno_kept: ``errno`` survived the repair.
        reason_kept: ``strerror`` survived the repair and is not empty.
    """

    is_oserror: bool
    filename_cleared: bool
    filename2_cleared: bool
    errno_kept: bool
    reason_kept: bool


def cause_facts(error: config.ConfigError) -> CauseFacts:
    """Reduce the cause a refusal is chained to, to the booleans arms may assert.

    THE EXCEPTION ITSELF IS NEVER RETURNED, only scalars derived from it. pytest
    rewrites an assertion to render the asserted EXPRESSION independently of its
    message, so a name that still held the cause would print the cause -
    ``filename`` included - the moment any arm below failed. Every field of the
    returned record is a bool, so even a rendering of the whole record discloses
    nothing.

    A cause that is absent or is not an OSError is reported as having no path
    and no reason, which is the reading that makes
    ``test_the_unreadable_records_cause_keeps_the_reason_it_failed`` red rather
    than green if the leak is ever closed by dropping the cause.

    Args:
        error: The refusal to read ``__cause__`` from.

    Returns:
        The five booleans.
    """
    cause = error.__cause__
    if not isinstance(cause, OSError):
        return CauseFacts(
            is_oserror=False,
            filename_cleared=True,
            filename2_cleared=True,
            errno_kept=False,
            reason_kept=False,
        )
    return CauseFacts(
        is_oserror=True,
        filename_cleared=cause.filename is None,
        filename2_cleared=cause.filename2 is None,
        errno_kept=cause.errno is not None,
        reason_kept=bool(cause.strerror),
    )


def needle_control() -> tuple[bool, str]:
    """Prove redact() rewrites :data:`RECORD_NEEDLE` before its absence is read.

    THE ORACLE IS IMPORTED DIRECTLY, which is stated here rather than left
    silent. ``clockspeed/surface/config.py`` deliberately binds no ``redact`` -
    it imports nothing from ``data`` and builds every refusal out of a closed
    vocabulary instead - so unlike ``tests/test_make_cert.py``, which borrows the
    script's own bound oracle, there is no module-bound one to borrow.

    Returns:
        Whether the needle is rewritten, and what it is rewritten to. The
        rewritten form is a placeholder rather than a path, so an assertion
        message may render it.
    """
    rewritten = redact(RECORD_NEEDLE)
    return rewritten != RECORD_NEEDLE and RECORD_NEEDLE not in rewritten, rewritten


def unreadable_record(tmp_path: Path) -> Path:
    """A record path that cannot be read, with the needle inside it.

    NOTHING IS PATCHED AND NOTHING IS CREATED. The parent directory is absent,
    so the operating system supplies the ENOENT and fills in the ``filename``
    field this section is about - the same shape arm (e) already uses, with a
    needle redact() can be proven to rewrite.

    Args:
        tmp_path: The per-test temporary root.

    Returns:
        The absent record, below an equally absent needle-named directory.
    """
    return tmp_path / RECORD_NEEDLE / "ports.json"


def test_a_missing_record_renders_no_path_through_the_default_excepthook(
    tmp_path: Path,
) -> None:
    """CS-857. The site's failure reaches the operator carrying no path.

    THE SITE IS DRIVEN DIRECTLY, IN A SUBPROCESS. What the process RENDERS is
    the subject, not the ``filename`` fields, and that distinction is the whole
    of this arm. A repair that cleared ``filename`` and ``filename2`` but left
    ``__suppress_context__`` false would still render the original underneath
    "During handling of the above exception", both paths intact. The sibling arm
    below, which reads the named fields, cannot see that channel at all; this
    one can, because it reads what a real interpreter really printed.

    NOTHING CAPTURED IS RENDERED. The captured streams carry the real tmp_path,
    so every assertion binds a boolean first and its message names only the
    synthetic needle and a fixed refusal line this module already owns.
    """
    redactable, rewritten = needle_control()
    missing = unreadable_record(tmp_path)

    done = subprocess.run(
        [sys.executable, "-c", RECORD_SITE_DRIVER, str(config.repo_root()), str(missing)],
        shell=False,
        capture_output=True,
        text=True,
        timeout=DRIVER_TIMEOUT_SECONDS,
        check=False,
    )
    survived = done.returncode == 0
    refused = config.RECORD_UNREADABLE in done.stderr
    leaked = RECORD_NEEDLE in (done.stdout + done.stderr)

    assert redactable, (
        f"redact() left {RECORD_NEEDLE} unchanged, so its absence below would be "
        "evidence of nothing"
    )
    assert not survived, (
        "the driver read a record that is supposed to be absent, so the site "
        "under test never raised and nothing here was measured"
    )
    assert refused, (
        "the driver died before reaching the refusal, so the absence of the "
        "needle below says nothing about the site"
    )
    assert not leaked, (
        f"the default excepthook rendered {RECORD_NEEDLE}, which redact() "
        f"rewrites to {rewritten}; the record read still hands a path to the "
        "renderer above it"
    )


def test_the_unreadable_records_cause_carries_no_filename(tmp_path: Path) -> None:
    """The named channel, read as fields rather than as a rendering.

    ``OSError.__str__`` appends ``filename`` and ``filename2`` verbatim, so
    these two fields are the leak the excepthook arm above measures. Reading
    them directly is what says the repair was made in the cause rather than
    papered over by a formatter that happened not to reach it.

    THIS ARM CANNOT SEE THE CONTEXT CHANNEL. Empty filename fields are not proof
    that the rendering is clean, which is precisely why the excepthook arm sits
    beside it. Neither arm is sufficient alone.
    """
    missing = unreadable_record(tmp_path)
    with pytest.raises(config.ConfigError) as caught:
        config.allocated_port(missing)
    facts = cause_facts(caught.value)

    assert facts.is_oserror, "the refusal is chained to no OSError, so this arm measured nothing"
    assert facts.filename_cleared, "the chained cause still carries the path it failed on"
    assert facts.filename2_cleared, "the chained cause still carries a second path"


def test_the_unreadable_records_cause_keeps_the_reason_it_failed(tmp_path: Path) -> None:
    """The other half of the contract - the diagnostic the repair must not drop.

    ERRNO AND STRERROR ARE ASSERTED PRESENT. A repair that closed the channel by
    dropping the cause, suppressing it, or replacing it with something that is
    not an OSError would pass every rendering arm above while costing the
    operator the only diagnostic there is. The wrapper's fixed line deliberately
    says neither which file nor why, so "absent" and "present but unreadable" -
    different faults with different remedies - are tellable apart here or
    nowhere.
    """
    missing = unreadable_record(tmp_path)
    with pytest.raises(config.ConfigError) as caught:
        config.allocated_port(missing)
    facts = cause_facts(caught.value)

    assert facts.is_oserror, "the refusal is chained to no OSError, so the reason is gone"
    assert facts.errno_kept, "the repair dropped errno, and with it why the read failed"
    assert facts.reason_kept, "the repair dropped strerror, and with it why the read failed"


def test_the_cause_reader_reports_a_dropped_cause_rather_than_passing_it(
    tmp_path: Path,
) -> None:
    """The detector, run against a planted negative - it must not pass vacuously.

    :func:`cause_facts` is used above to prove an ABSENCE, so it is also run here
    against a refusal chained to nothing at all. A reader that reported a missing
    cause as clean-and-complete would turn the two arms above green for a repair
    that deleted the diagnostic, which is the failure mode this section exists to
    make impossible (CONVENTIONS.md section 7.2).
    """
    missing = unreadable_record(tmp_path)
    with pytest.raises(config.ConfigError) as caught:
        config.allocated_port(missing)
    dropped = config.ConfigError(caught.value.fault)
    facts = cause_facts(dropped)

    assert not facts.is_oserror, "a refusal chained to nothing was read as carrying an OSError"
    assert not facts.errno_kept, "a refusal chained to nothing was read as keeping errno"
    assert not facts.reason_kept, "a refusal chained to nothing was read as keeping a reason"
