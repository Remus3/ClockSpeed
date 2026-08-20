"""The work directory: the only writer in the save package, proven read-only at its source.

WHAT THIS MODULE IS FOR. ``clockspeed/save/workdir.py`` holds the single write
in ``clockspeed/save/`` (docs/ARCHITECTURE.md section 1.1, docs/adr/0007
Decision item 6). Everything here exists to make the never-write invariant
(CLAUDE.md non-negotiable 1, memory/never-write-to-the-game.md) a MEASURED
property rather than a reviewed one.

The invariant has two halves and both are covered below:

- **The source is never written.** Proven twice, deliberately by two unrelated
  mechanisms. ``test_the_source_is_untouched_by_the_copy`` compares size,
  ``st_mtime_ns`` and sha256 across the copy; ``st_mtime_ns`` is the field that
  catches an accidental open-for-append, which a size or hash check alone would
  miss on a re-written identical byte. ``test_no_write_intent_event_reaches_the
  _save_root`` installs an audit hook in a child interpreter and watches the
  interpreter's own event stream instead. A single check would be one bug away
  from vacuous; these two fail for different reasons.
- **The destination is never inside the save root or the install.** A copy
  written back into the save directory would violate the invariant just as
  surely as an in-place parse, so ``copy_for_read`` refuses, and the refusal is
  tested against a plain path, a ``..`` traversal and a symlink.

NOTHING HERE TOUCHES THE REAL MACHINE. The ``isolate_from_the_real_machine``
fixture is autouse, so every test in this module runs with all four
``CLOCKSPEED_*`` overrides pointed at a path asserted not to exist. That is
structural rather than per-test on purpose: a test that forgot to isolate
itself would silently read the operator's real save directory on the one
machine where the mistake is invisible - the machine where the game IS
installed, because there it passes.

WHY THE COUNTS IN THE AUDIT TEST MATTER. Asserting only "no writes happened"
passes for a function that does nothing at all. The read-open count is asserted
non-zero in the same test for that reason; it is what proves the hook was
actually watching a function that actually ran.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.data import locate
from clockspeed.data.locate import (
    ENV_ACCOUNT_DIR,
    ENV_GAME_DIR,
    ENV_LOCAL_CONFIG,
    ENV_SAVE_ROOT,
)
from clockspeed.save import workdir
from tests.save import reach_guard, synthetic

# ---------------------------------------------------------------------------
# Paths, derived rather than written down
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
THIS_MODULE = Path(__file__).resolve()

# The path every override points at. Under the repo root rather than under a
# temporary directory so it needs no fixture and is identical in every child,
# and asserted absent below so it can never quietly become real and turn the
# isolation into a no-op. Same device, same reasoning, as
# tests/data/test_phase2_gate.py::ABSENT.
ABSENT = REPO_ROOT / "no-such-path-workdir-suite"

# A synthetic stand-in for the account directory. Ten digits, which is at or
# above clockspeed.data.locate.MIN_ACCOUNT_ID_DIGITS, so redact() treats it the
# way it treats a real one - which is what lets the redaction test below assert
# that these exact characters do NOT survive into a message. It is invented.
PRETEND_ACCOUNT = "1234567890"

# A SECOND stand-in, beside the first rather than instead of it - PRETEND_ACCOUNT
# carries roughly eight other assertions in this module and none of them are
# about shape. This one is a hex token: not digits, so the digit-run backstop
# cannot reach it, which is what makes it able to observe a rule the all-digit
# fixture cannot (CS-454). The save root here is relocated - "pretend_saves"
# spells no FactoryGame/Saved/SaveGames marker - so the positional rule has
# nothing to key on either, and between them those two facts are what stop a
# control on this name from being carried by a rule it does not name. Invented.
PRETEND_NONDIGIT_ACCOUNT = "b7c1e0a4d5f6928374a5b6c7d8e9f012"

_CHILD_TIMEOUT_SECONDS = 300

# Expected counts, named so the assertions read as contracts rather than as
# magic numbers.
EXPECT_NONE = 0
EXPECT_AT_LEAST_ONE = 1

# A write-capable open, found by extracting the MODE argument and testing it,
# rather than by looking for a mode character anywhere inside the call. The
# naive form matches open("data.txt") on the "a" in "data" and reports a read
# as a write; this one cannot, because it only ever inspects the captured mode.
WRITE_MODE_CHARS = frozenset("wax+")
_DOT_OPEN = re.compile(r"""\.open\s*\(\s*(["'])([^"']*)\1""")
_BUILTIN_OPEN = re.compile(r"""(?<![.\w])open\s*\([^,()]*,\s*(["'])([^"']*)\1""")


def write_modes_in(text: str) -> list[str]:
    """Return every file mode in ``text`` that a file could be written through."""
    modes = [
        match.group(2) for pattern in (_DOT_OPEN, _BUILTIN_OPEN) for match in pattern.finditer(text)
    ]
    return [mode for mode in modes if WRITE_MODE_CHARS & set(mode)]


# ---------------------------------------------------------------------------
# Isolation
# ---------------------------------------------------------------------------


def test_the_forced_absent_path_really_is_absent() -> None:
    """If ABSENT ever became real, every isolation assertion below is vacuous."""
    assert not ABSENT.exists(), (
        f"{ABSENT.name} exists, so the no-install overrides resolve to something real"
    )


@pytest.fixture(autouse=True)
def isolate_from_the_real_machine(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point every resolver at nothing, for every test in this module.

    All four overrides, not just the two that name a save location.
    ``CLOCKSPEED_LOCAL_CONFIG`` is the one that is easy to forget and the one
    that matters most: without it, ``locate.local_config()`` reads the
    operator's real ``config/local.json`` and a "pretend" save root quietly
    becomes the real one.

    THE REDACTION MEMORIES ARE RESET HERE, AND THAT IS NOT HOUSEKEEPING - it is
    the difference between a control and a control-shaped no-op (CS-454).
    ``locate`` remembers every account directory and every save root it hands
    out, as module state that outlives a test. This module had no reset, so a
    neighbour seeded the memory for the whole process:
    ``test_a_destination_inside_the_account_directory_is_refused`` points
    ``CLOCKSPEED_ACCOUNT_DIR`` at a real directory, which makes that name a
    redaction needle for every test that runs after it.

    That was not reasoned, it was measured: with the digit-run backstop
    neutered, a redaction control in this module passed in a full-module run
    and FAILED when run alone, because alone there was no neighbour to seed the
    needle. NO COUNTS ARE QUOTED HERE ON PURPOSE - the figures belonged to a
    tree that no longer exists, and a measured number in prose is a lie with a
    timestamp on it (CLAUDE.md section 4). Re-derive it against whatever tree
    you are reading, by running one such control alone and then with the file.

    The direction of the hazard is what makes it worth a fixture rather than a
    comment: under ``-n auto`` the seeding test and the control may land in
    different workers, so the vacuity is NONDETERMINISTIC, which is the shape
    that survives review.

    Replacing the ATTRIBUTE through monkeypatch restores it automatically,
    which calling a reset helper would not.
    """
    monkeypatch.setenv(ENV_GAME_DIR, str(ABSENT / "install"))
    monkeypatch.setenv(ENV_SAVE_ROOT, str(ABSENT / "saves"))
    monkeypatch.setenv(ENV_ACCOUNT_DIR, str(ABSENT / "account"))
    monkeypatch.setenv(ENV_LOCAL_CONFIG, str(ABSENT / "local.json"))
    monkeypatch.setattr(locate, "_RESOLVED_ACCOUNT_NAMES", [])
    monkeypatch.setattr(locate, "_RESOLVED_SAVE_ROOTS", [])
    # An operator who has this set in their shell would otherwise change where
    # the default-work-root test looks.
    monkeypatch.delenv(workdir.ENV_WORK_ROOT, raising=False)


# ---------------------------------------------------------------------------
# Fixtures - synthetic bytes and a pretend save root, never a real one
# ---------------------------------------------------------------------------


@pytest.fixture
def save_bytes() -> bytes:
    """A whole synthetic save. Invented bytes, built in-repo, never a real save."""
    return synthetic.build_save()


@pytest.fixture
def pretend_save_root(tmp_path: Path) -> Path:
    """A stand-in save root with an account directory beneath it."""
    root = tmp_path / "pretend_saves"
    (root / PRETEND_ACCOUNT).mkdir(parents=True)
    return root


@pytest.fixture
def pretend_account_dir(pretend_save_root: Path) -> Path:
    """The account directory beneath the pretend save root."""
    return pretend_save_root / PRETEND_ACCOUNT


@pytest.fixture
def pretend_source(pretend_account_dir: Path, save_bytes: bytes) -> Path:
    """A synthetic save sitting where a real one would sit."""
    source = pretend_account_dir / "SyntheticWorld.sav"
    source.write_bytes(save_bytes)
    return source


@pytest.fixture
def work(tmp_path: Path) -> Path:
    """A work root well outside the pretend save root."""
    return tmp_path / "work"


def sha256_of(path: Path) -> str:
    """Hash a file's bytes. Compared instead of length, per the acceptance criteria."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stat_triple(path: Path) -> tuple[int, int, str]:
    """Return (size, st_mtime_ns, sha256) - the three fields asserted unchanged."""
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns, sha256_of(path)


# ===========================================================================
# 1. The copy is byte-identical
# ===========================================================================


def test_the_copy_is_byte_identical_to_the_source(pretend_source: Path, work: Path) -> None:
    """sha256 of the copy equals sha256 of the source, and it lands under the work root."""
    copy = workdir.copy_for_read(pretend_source, work_root=work)

    assert copy.is_file(), "copy_for_read returned a path that is not a file"
    assert copy.resolve().is_relative_to(work.resolve()), "the copy landed outside the work root"
    assert sha256_of(copy) == sha256_of(pretend_source), "the copy is not byte-identical"


def test_the_copy_survives_a_body_with_every_byte_value(
    pretend_account_dir: Path, work: Path
) -> None:
    """A binary-safe copy, proven on bytes a text-mode copy would mangle.

    ``0x0D 0x0A`` is the pair that a file opened in text mode rewrites on
    Windows, and a save is full of them. This is the sibling case of the hash
    test: same root cause, different input.
    """
    source = pretend_account_dir / "AllBytes.sav"
    source.write_bytes(bytes(range(256)) * 8)

    copy = workdir.copy_for_read(source, work_root=work)

    assert copy.read_bytes() == source.read_bytes(), "the copy is not binary-safe"


# ===========================================================================
# 2. The source is provably untouched
# ===========================================================================


def test_the_source_is_untouched_by_the_copy(pretend_source: Path, work: Path) -> None:
    """Size, st_mtime_ns and sha256 are all identical across the copy.

    ``st_mtime_ns`` is the load-bearing one. A file opened for append and then
    closed without a write has the same size and the same hash; only the
    modification time moves. Nanoseconds rather than seconds because a
    whole-second field is too coarse to see a change made microseconds ago.
    """
    before = stat_triple(pretend_source)

    workdir.copy_for_read(pretend_source, work_root=work)

    after = stat_triple(pretend_source)
    assert after[0] == before[0], "the source size changed"
    assert after[1] == before[1], "the source modification time changed - it was opened for write"
    assert after[2] == before[2], "the source bytes changed"


def test_repeated_copies_leave_the_source_untouched(pretend_source: Path, work: Path) -> None:
    """The invariant holds under repetition, not only on the first call."""
    before = stat_triple(pretend_source)

    for _ in range(3):
        workdir.copy_for_read(pretend_source, work_root=work)

    assert stat_triple(pretend_source) == before, "a repeated copy disturbed the source"


# ===========================================================================
# 3. The destination refusal
# ===========================================================================


def test_a_destination_inside_the_save_root_is_refused(
    pretend_source: Path, pretend_save_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A work root inside the save root is refused - this is the never-write rule in code."""
    monkeypatch.setenv(ENV_SAVE_ROOT, str(pretend_save_root))

    with pytest.raises(workdir.DestinationRefusedError):
        workdir.copy_for_read(pretend_source, work_root=pretend_save_root / "work")


def test_a_destination_inside_the_account_directory_is_refused(
    pretend_source: Path,
    pretend_save_root: Path,
    pretend_account_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The account directory is refused too, not merely the save root above it."""
    monkeypatch.setenv(ENV_SAVE_ROOT, str(pretend_save_root))
    monkeypatch.setenv(ENV_ACCOUNT_DIR, str(pretend_account_dir))

    with pytest.raises(workdir.DestinationRefusedError):
        workdir.copy_for_read(pretend_source, work_root=pretend_account_dir / "work")


def test_a_destination_inside_the_game_install_is_refused(
    pretend_source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The install is read-only material and is refused as a destination."""
    install = tmp_path / "pretend_install"
    install.mkdir()
    monkeypatch.setenv(ENV_GAME_DIR, str(install))

    with pytest.raises(workdir.DestinationRefusedError):
        workdir.copy_for_read(pretend_source, work_root=install / "work")


def test_a_destination_reaching_the_save_root_by_traversal_is_refused(
    pretend_source: Path, pretend_save_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A '..' traversal must not defeat the check - both sides are resolved first.

    The path spelled here is lexically outside the save root and resolves to
    somewhere inside it. A check written against the string rather than against
    the resolved path passes this and writes into the save directory.
    """
    monkeypatch.setenv(ENV_SAVE_ROOT, str(pretend_save_root))
    traversal = pretend_save_root / "sibling" / ".." / PRETEND_ACCOUNT / "work"

    with pytest.raises(workdir.DestinationRefusedError):
        workdir.copy_for_read(pretend_source, work_root=traversal)


def test_a_destination_reaching_the_save_root_by_symlink_is_refused(
    pretend_source: Path,
    pretend_save_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A symlink pointing into the save root must not defeat the check either.

    SKIPS WITH A REASON where the platform will not create a symlink unelevated
    - Windows needs Developer Mode or an elevated process. A skip keeps the
    exit code at zero and stays visible in the ``-ra`` summary, which is the
    project's rule for a test that cannot run here rather than one that has
    been quietly deleted.
    """
    monkeypatch.setenv(ENV_SAVE_ROOT, str(pretend_save_root))
    link = tmp_path / "link_into_saves"
    try:
        link.symlink_to(pretend_save_root, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"this platform will not create a directory symlink here: {type(exc).__name__}")

    with pytest.raises(workdir.DestinationRefusedError):
        workdir.copy_for_read(pretend_source, work_root=link / "work")


def test_a_refused_destination_is_not_created(
    pretend_source: Path, pretend_save_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The refusal happens BEFORE any directory is made.

    Ordering is the whole point. A check that ran after mkdir would already
    have written into the save directory by the time it refused, and the
    exception would be a report of a violation rather than a prevention of one.
    """
    monkeypatch.setenv(ENV_SAVE_ROOT, str(pretend_save_root))
    forbidden = pretend_save_root / "work"

    with pytest.raises(workdir.DestinationRefusedError):
        workdir.copy_for_read(pretend_source, work_root=forbidden)

    assert not forbidden.exists(), "the refusal created the directory it was refusing"


def test_a_permitted_destination_outside_both_roots_is_allowed(
    pretend_source: Path, pretend_save_root: Path, work: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The refusal is narrow. A guard that refused everything would pass every test above."""
    monkeypatch.setenv(ENV_SAVE_ROOT, str(pretend_save_root))

    copy = workdir.copy_for_read(pretend_source, work_root=work)

    assert copy.is_file(), "a legitimate destination outside both roots was refused"


def test_the_refusal_message_carries_no_raw_account_directory(
    pretend_source: Path, pretend_save_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every path in an exception goes through locate.redact() first.

    Asserted on the rendered message rather than on the call, because the leak
    this prevents happens at the render site. The account directory name is a
    platform account id (CLAUDE.md non-negotiable 3) and a message quoting one
    into a log or an issue is the leak.
    """
    monkeypatch.setenv(ENV_SAVE_ROOT, str(pretend_save_root))

    with pytest.raises(workdir.DestinationRefusedError) as caught:
        workdir.copy_for_read(pretend_source, work_root=pretend_save_root / PRETEND_ACCOUNT)

    message = str(caught.value)
    assert PRETEND_ACCOUNT not in message, "the refusal message leaks the account directory"
    assert "\\" not in message, "the message was not passed through redact()"


def test_the_refusal_message_carries_no_raw_account_directory_of_a_non_digit_shape(
    pretend_source: Path, pretend_save_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The same refusal, against the shape the fixture above cannot observe.

    THE CONJUNCTION, and every clause is load-bearing (CS-454):

      (a) the account name is a HEX TOKEN. The test above uses ten digits,
          which is at or above ``locate.MIN_ACCOUNT_ID_DIGITS``, so the
          digit-run backstop catches it unconditionally and the test cannot
          fail for any other reason. Epic writes a hex token, the Microsoft
          Store a GUID, and the override writes whatever the operator typed.
      (b) the save root is RELOCATED - ``pretend_saves`` spells no
          FactoryGame/Saved/SaveGames marker, asserted below rather than
          assumed - so the POSITIONAL rule has nothing to key on. Without this
          clause position would fire and mask the shape entirely, and the test
          would be green about a rule it does not name.
      (c) the rule under mutation is therefore the save-root ANCHOR set.
          Remove it and this hex token stands in the refusal message in
          plaintext.

    Asserted on the rendered message, not the call: the leak happens where the
    exception is rendered into a log or an issue.
    """
    account = pretend_save_root / PRETEND_NONDIGIT_ACCOUNT
    account.mkdir()
    monkeypatch.setenv(ENV_SAVE_ROOT, str(pretend_save_root))
    assert "FactoryGame/Saved/SaveGames" not in pretend_save_root.as_posix(), (
        "the pretend save root spells the marker, so POSITION would fire and this "
        "test would prove nothing about the shape it names"
    )

    with pytest.raises(workdir.DestinationRefusedError) as caught:
        workdir.copy_for_read(pretend_source, work_root=account / "work")

    message = str(caught.value)
    assert PRETEND_NONDIGIT_ACCOUNT not in message, (
        "the refusal message leaks a non-digit account directory"
    )
    assert f"/pretend_saves/{locate.ACCOUNT_DIR_PLACEHOLDER}/work/" in message, (
        "the account directory went, but so did the structure around it - the "
        "placeholder has to sit between the save root and the work directory, or a "
        "negative assertion alone rules out without pinning down (CONVENTIONS.md "
        "section 7.2)"
    )


# ===========================================================================
# 3a. CS-444 - a forbidden root that is there and will not resolve
# ===========================================================================
#
# THE DEFECT. ``_forbidden_roots`` used to append a candidate only when
# ``_resolved`` handed back a path, so a root the resolver had already
# confirmed - and which therefore exists - left the refuse list entirely when
# its resolution failed. The guard then had nothing to compare against and the
# copy proceeded. The failure direction is a WRITE, and it is a write into the
# one place non-negotiable 1 names, reached through the module the architecture
# picked as the package's single writer.
#
# WHY THESE TESTS PATCH THE RESOLVER INSTEAD OF BUILDING AN UNRESOLVABLE PATH.
# The failures ``_resolved`` catches - a symlink loop, an embedded NUL, a path
# past the platform's length limit - are raised or swallowed differently across
# operating systems and across interpreter versions, and this project's
# declared floor is not the interpreter these tests were measured on. A test
# built on one of them would be asserting something about this machine while
# reading as an assertion about the guard. What CS-444 is about is what the two
# functions DO once a resolution has come back None, so that is forced
# directly.
#
# THE STAND-IN IS SURGICAL, AND THAT IS LOAD-BEARING RATHER THAN TIDY.
# ``_refuse_if_forbidden`` resolves the DESTINATION through the same helper and
# already refused when that came back None, so a stand-in answering None for
# everything would refuse for the pre-existing reason and pass against the very
# code these tests exist to fail against.
# ``test_the_unresolvable_root_harness_refuses_nothing_by_itself`` grades that.


def resolver_that_fails_only_for(target: Path) -> Callable[[Path], Path | None]:
    """Return a ``_resolved`` stand-in that answers None for one path only.

    Args:
        target: The single path whose resolution fails.

    Returns:
        A callable with ``_resolved``'s signature that hands every other path
        to the real implementation.
    """
    real = workdir._resolved  # noqa: SLF001

    def resolver(path: Path) -> Path | None:
        return None if Path(path) == target else real(path)

    return resolver


def test_a_forbidden_root_that_does_not_resolve_is_still_reported(
    pretend_save_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """REPORTED is half of CS-444's acceptance, and it is graded on its own here.

    A fix that refused without reporting would leave a caller unable to say
    WHICH root went unchecked, and the label is the only safe way to say that -
    the path itself is personal data.
    """
    monkeypatch.setenv(ENV_SAVE_ROOT, str(pretend_save_root))
    monkeypatch.setattr(workdir, "_resolved", resolver_that_fails_only_for(pretend_save_root))

    roots = workdir._forbidden_roots()  # noqa: SLF001

    assert roots, (
        "a forbidden root that is present and did not resolve was dropped from the refuse "
        "list, so nothing downstream can tell it was left unchecked"
    )
    unchecked = [root.label for root in roots if root.resolved is None]
    assert unchecked == [workdir.LABEL_SAVE_ROOT], (
        "the root that did not resolve is not reported under its own label"
    )


def test_a_forbidden_root_that_does_not_resolve_refuses_the_copy(
    pretend_source: Path,
    pretend_save_root: Path,
    work: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """STILL FORBIDDEN is the other half, and it is the half that stops the write.

    The destination here sits well outside the save root, so this is not a test
    that the comparison works - it is a test that a root which cannot be
    compared against refuses on its own. The reason is the same one
    ``_refuse_if_forbidden`` already applies to an unresolvable DESTINATION:
    what is missing is the proof that the copy lands outside, and a check whose
    proof is missing refuses.
    """
    monkeypatch.setenv(ENV_SAVE_ROOT, str(pretend_save_root))
    monkeypatch.setattr(workdir, "_resolved", resolver_that_fails_only_for(pretend_save_root))

    with pytest.raises(workdir.DestinationRefusedError):
        workdir.copy_for_read(pretend_source, work_root=work)


def test_a_copy_refused_for_an_unresolvable_root_creates_nothing(
    pretend_source: Path,
    pretend_save_root: Path,
    work: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The refusal lands before the mkdir, as it does for the destination check.

    Same argument as ``test_a_refused_destination_is_not_created``: a refusal
    raised after the directory existed would report a violation rather than
    prevent one.
    """
    monkeypatch.setenv(ENV_SAVE_ROOT, str(pretend_save_root))
    monkeypatch.setattr(workdir, "_resolved", resolver_that_fails_only_for(pretend_save_root))

    with pytest.raises(workdir.DestinationRefusedError):
        workdir.copy_for_read(pretend_source, work_root=work)

    assert not work.exists(), "the refusal created the work directory it was refusing"


def test_the_unresolvable_root_refusal_names_the_root_and_renders_no_path(
    pretend_source: Path,
    pretend_save_root: Path,
    work: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The message says which root could not be checked, using its fixed label.

    A refusal that did not name the root would send an operator hunting through
    three resolvers, and a refusal that named it by PATH would render the thing
    non-negotiable 3 forbids rendering.
    """
    monkeypatch.setenv(ENV_SAVE_ROOT, str(pretend_save_root))
    monkeypatch.setattr(workdir, "_resolved", resolver_that_fails_only_for(pretend_save_root))

    with pytest.raises(workdir.DestinationRefusedError) as caught:
        workdir.copy_for_read(pretend_source, work_root=work)

    message = str(caught.value)
    assert workdir.LABEL_SAVE_ROOT in message, (
        "the refusal does not say which root it could not check"
    )
    assert PRETEND_ACCOUNT not in message, "the refusal message leaks the account directory"
    assert "\\" not in message, "the message was not passed through redact()"


def test_the_unresolvable_root_harness_refuses_nothing_by_itself(
    pretend_source: Path,
    pretend_save_root: Path,
    work: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The stand-in the four tests above rest on is graded rather than trusted.

    Pointed at a path that is neither a forbidden root nor the destination nor
    the source, it must change the outcome not at all. Without this, a stand-in
    that answered None too widely would make those tests pass for the
    pre-existing unresolvable-destination reason and CS-444 would look fixed
    while the hole stayed open.
    """
    monkeypatch.setenv(ENV_SAVE_ROOT, str(pretend_save_root))
    monkeypatch.setattr(workdir, "_resolved", resolver_that_fails_only_for(work / "unrelated"))

    copy = workdir.copy_for_read(pretend_source, work_root=work)

    assert copy.is_file(), "the stand-in resolver changed an outcome it was not aimed at"


def test_a_root_that_is_absent_is_not_reported_as_one_that_would_not_resolve() -> None:
    """A machine with no game installed stays a supported state, not a refusal.

    Two different facts share the value None and CS-444's fix must keep them
    apart. A resolver answering None means there is no such root here, so there
    is nothing to forbid; a resolver answering a path that then fails to
    resolve means the root is there and could not be checked. The autouse
    isolation points all four overrides at a path asserted absent, so this is
    the first case, and the refuse list stays empty.

    This one passes against the pre-fix code too. It is the fence that stops
    the fix over-reaching into a refusal on every machine with no game, not a
    reproduction of the defect.
    """
    assert workdir._forbidden_roots() == []  # noqa: SLF001


# ===========================================================================
# The error surface
# ===========================================================================


def test_the_error_types_share_one_base() -> None:
    """A caller can catch WorkDirError and be sure it caught all of them."""
    assert issubclass(workdir.SourceUnreadableError, workdir.WorkDirError)
    assert issubclass(workdir.DestinationRefusedError, workdir.WorkDirError)


def test_a_missing_source_raises_source_unreadable(tmp_path: Path, work: Path) -> None:
    """An absent source is a stated error, not an OSError leaking from the copy."""
    with pytest.raises(workdir.SourceUnreadableError):
        workdir.copy_for_read(tmp_path / "no-such-file.sav", work_root=work)


def test_a_directory_given_as_a_source_raises_source_unreadable(tmp_path: Path, work: Path) -> None:
    """A directory is not a readable save, and says so rather than half-copying."""
    with pytest.raises(workdir.SourceUnreadableError):
        workdir.copy_for_read(tmp_path, work_root=work)


def test_a_missing_source_message_carries_no_raw_path(
    pretend_account_dir: Path, work: Path
) -> None:
    """The unreadable-source message is redacted too, not only the refusal message."""
    with pytest.raises(workdir.SourceUnreadableError) as caught:
        workdir.copy_for_read(pretend_account_dir / "Absent.sav", work_root=work)

    message = str(caught.value)
    assert PRETEND_ACCOUNT not in message, "the message leaks the account directory"
    assert "\\" not in message, "the message was not passed through redact()"


# ===========================================================================
# 4. latest_save across manual saves and autosaves
# ===========================================================================


def write_with_mtime(path: Path, payload: bytes, mtime_ns: int) -> Path:
    """Create a file with an exact modification time.

    Set explicitly rather than by sleeping between writes: an ordering test
    that depends on wall-clock granularity is the flaky test this avoids.
    """
    path.write_bytes(payload)
    os.utime(path, ns=(mtime_ns, mtime_ns))
    return path


def test_latest_save_picks_the_newest_across_manual_saves_and_autosaves(
    pretend_account_dir: Path, save_bytes: bytes
) -> None:
    """The newest wins whether it is a manual save or an autosave.

    Both live in the same directory and differ only by filename
    (BOOTSTRAP.md section 8.2 and the naming row in section 2), so the winner
    here is an autosave sitting between two manual saves in time.
    """
    base = 1_600_000_000_000_000_000
    write_with_mtime(pretend_account_dir / "World_010101-000000.sav", save_bytes, base)
    write_with_mtime(pretend_account_dir / "World_020202-000000.sav", save_bytes, base + 2_000)
    newest = write_with_mtime(
        pretend_account_dir / "World_autosave_1.sav", save_bytes, base + 9_000
    )
    write_with_mtime(pretend_account_dir / "World_autosave_0.sav", save_bytes, base + 1_000)

    assert workdir.latest_save(pretend_account_dir) == newest


def test_latest_save_picks_a_manual_save_when_it_is_the_newest(
    pretend_account_dir: Path, save_bytes: bytes
) -> None:
    """The mirror of the test above, so neither kind is preferred by construction."""
    base = 1_600_000_000_000_000_000
    write_with_mtime(pretend_account_dir / "World_autosave_0.sav", save_bytes, base)
    newest = write_with_mtime(
        pretend_account_dir / "World_030303-000000.sav", save_bytes, base + 5_000
    )

    assert workdir.latest_save(pretend_account_dir) == newest


def test_latest_save_ignores_files_that_are_not_saves(
    pretend_account_dir: Path, save_bytes: bytes
) -> None:
    """A newer non-save file does not win. Only .sav is a save."""
    base = 1_600_000_000_000_000_000
    newest_save = write_with_mtime(pretend_account_dir / "World.sav", save_bytes, base)
    write_with_mtime(pretend_account_dir / "notes.txt", b"not a save", base + 9_000)

    assert workdir.latest_save(pretend_account_dir) == newest_save


def test_latest_save_returns_none_for_an_empty_directory(pretend_account_dir: Path) -> None:
    """Absent content is reported, never fatal (CLAUDE.md non-negotiable 7)."""
    assert workdir.latest_save(pretend_account_dir) is None


def test_latest_save_returns_none_for_an_absent_directory(tmp_path: Path) -> None:
    """A directory that does not exist returns None rather than raising."""
    assert workdir.latest_save(tmp_path / "no-such-directory") is None


def test_latest_save_returns_none_when_nothing_resolves() -> None:
    """With no account directory resolvable, the answer is None, not an exception.

    This is the state of a machine that has never had the game installed, which
    the whole suite has to run green on. The autouse fixture is what forces
    that state here, on a machine where the game IS installed.
    """
    assert workdir.latest_save() is None


def test_latest_save_is_stable_across_two_runs(
    pretend_account_dir: Path, save_bytes: bytes
) -> None:
    """Two runs over the same directory agree, including on a modification-time tie.

    An advisor that disagrees with itself between runs is a bug (CLAUDE.md
    section 1), and a tie broken by directory order is exactly how that
    happens. The tie is constructed here rather than hoped for.
    """
    base = 1_600_000_000_000_000_000
    for name in ("Bravo.sav", "Alpha.sav", "Charlie.sav"):
        write_with_mtime(pretend_account_dir / name, save_bytes, base)

    first = workdir.latest_save(pretend_account_dir)
    second = workdir.latest_save(pretend_account_dir)
    assert first == second, "two runs over one directory disagreed"
    assert first is not None
    assert first.name == "Alpha.sav", "the tiebreak is not the documented one"


# ===========================================================================
# 4b. The listing REPORTS what it could not read (CS-438)
# ===========================================================================
#
# THE DEFECT. ``_save_files`` returned a bare list, so a SHORT list had two
# indistinguishable causes: the directory really held nothing, or something in
# the way of reading it was swallowed. Its own docstring said "absent content is
# reported, never fatal" while nothing was reported anywhere. The fix is the
# report, not the raise - fail-soft is deliberate here (docs/ARCHITECTURE.md,
# and tests/save/test_phase4_gate.py depends on it for its audit spy).
#
# THE SECOND DEFECT, FOUND BY THE ADVERSARY THAT REFUTED THE FIRST BUILD. A
# report that FIRES is not a report that says something TRUE. One code and one
# fixed sentence covered absent, not-a-directory and refused together, and that
# sentence - "an empty result is not evidence that it holds no saves" - is FALSE
# of the first two. Absence IS evidence that there are no saves, and absence is
# the case that fires on every machine with no game installed, so the common
# path carried the false line. That is the CS-430 failure class reproduced
# inside the fix that cited CS-430. The conditions are therefore split by errno,
# each carries a sentence true of itself, and the tests below assert on the
# sentence's CONTENT rather than merely on a problem having appeared.
#
# WHICH FAULTS HERE ARE REAL AND WHICH ARE INJECTED, stated because the two are
# worth different amounts. REAL, needing no monkeypatch: a broken symlink named
# like a save is an entry ``Path.stat()`` refuses; a plain file is a path
# ``Path.iterdir()`` refuses; an absent path is another. INJECTED: the REFUSED
# cases, because no condition producing a non-ignored errno inside a listable
# directory was reproducible on this platform - see
# ``test_stat_reports_the_broken_symlink_fault_that_is_file_hides`` for what
# that costs and what it does not.


def make_broken_symlink(path: Path) -> Path:
    """Create a symlink to a target that does not exist, or skip the test.

    Skips with a reason where the platform will not create one - Windows needs
    Developer Mode or an elevated process - on the same terms as
    ``test_a_destination_reaching_the_save_root_by_symlink_is_refused``.
    """
    try:
        path.symlink_to(path.parent / "no-such-target")
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"this platform will not create a symlink here: {type(exc).__name__}")
    return path


def refuse(monkeypatch: pytest.MonkeyPatch, method: str, target: Path) -> None:
    """Make one ``Path`` method fail with EACCES for exactly one path.

    THIS FAULT IS INJECTED AND THE OTHERS ARE NOT, which is worth saying out
    loud. A directory or an entry that is PRESENT and REFUSED is the only
    condition under which the reports below claim ignorance rather than
    absence, and it is trivial to produce on POSIX and was not reproducible
    here. Injecting it tests the classification and the wording, which is what
    the reports are; it does not establish that Windows ever produces it.

    The raised error carries the real path in ``filename``, ``strerror`` and
    ``args`` on purpose, so the privacy tests below are rendering something
    that genuinely had a path in it.

    Args:
        monkeypatch: The pytest fixture, which undoes this after the test.
        method: The ``Path`` method to refuse - ``iterdir`` or ``stat``.
        target: The one path that gets the refusal. Everything else is
            forwarded to the real method, so the rest of the scan still runs.
    """
    real = getattr(Path, method)

    def refusing(self: Path, *args: object, **kwargs: object) -> object:
        if self == target:
            raise PermissionError(errno.EACCES, "Permission denied", str(self))
        return real(self, *args, **kwargs)

    monkeypatch.setattr(Path, method, refusing)


def only_with_errno(listing: workdir.SaveListing, code: int) -> workdir.ListingProblem:
    """Return the one problem carrying ``code``, and assert there is exactly one.

    Selecting by ERRNO rather than by position, because a directory listing's
    order is the filesystem's business and an index would silently grade the
    wrong entry - which is exactly what one draft of these tests did.
    """
    matching = [problem for problem in listing.problems if problem.errno == code]
    assert len(matching) == EXPECT_AT_LEAST_ONE, (
        f"expected exactly one problem with errno {code}, got "
        f"{[problem.errno for problem in listing.problems]}"
    )
    return matching[0]


def test_an_empty_directory_lists_nothing_and_reports_no_problem(
    pretend_account_dir: Path,
) -> None:
    """The baseline the failure cases below have to be distinguishable FROM."""
    listing = workdir._save_files(pretend_account_dir)  # noqa: SLF001

    assert listing.saves == ()
    assert listing.problems == (), "an empty directory is not a failure and must report none"
    assert listing.is_complete


def test_a_directory_that_can_be_listed_reports_nothing(
    pretend_account_dir: Path, save_bytes: bytes
) -> None:
    """NON-VACUITY. A reporter that reported always would pass every test below."""
    write_with_mtime(pretend_account_dir / "World.sav", save_bytes, 1_600_000_000_000_000_000)

    listing = workdir._save_files(pretend_account_dir)  # noqa: SLF001

    assert len(listing.saves) == EXPECT_AT_LEAST_ONE
    assert listing.problems == ()
    assert listing.is_complete


def test_a_directory_named_like_a_save_is_skipped_without_a_report(
    pretend_account_dir: Path,
) -> None:
    """A skip that is UNDERSTOOD is not a problem, and must not be reported as one.

    A directory called ``Fake.sav`` stats cleanly and is simply not a regular
    file. Reporting it would make the report mean "something was skipped"
    instead of "something could not be read", which is the weaker claim.
    """
    (pretend_account_dir / "Fake.sav").mkdir()

    listing = workdir._save_files(pretend_account_dir)  # noqa: SLF001

    assert listing.saves == ()
    assert listing.problems == ()
    assert listing.is_complete


def test_a_directory_that_cannot_be_listed_is_reported_not_silently_empty(
    pretend_account_dir: Path, save_bytes: bytes
) -> None:
    """THE CS-438 ACCEPTANCE. A read failure and an empty directory stop being one answer.

    Both produce zero saves. Before the report existed that was the whole
    answer, so a caller had no way to tell "there are no saves here" from "I
    could not look".
    """
    not_a_directory = pretend_account_dir / "World.sav"
    not_a_directory.write_bytes(save_bytes)
    genuinely_empty = pretend_account_dir / "empty"
    genuinely_empty.mkdir()

    failed = workdir._save_files(not_a_directory)  # noqa: SLF001
    empty = workdir._save_files(genuinely_empty)  # noqa: SLF001

    # The two agree on the saves and DISAGREE on the report. That disagreement
    # is the entire point of the item.
    assert failed.saves == empty.saves == ()
    assert [problem.code for problem in failed.problems] == [workdir.LISTING_DIRECTORY_ABSENT]
    assert empty.problems == ()
    assert failed.problems[0].errno is not None, "the report carries no errno to act on"


def test_the_three_directory_conditions_do_not_report_the_same_thing(
    pretend_account_dir: Path, save_bytes: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE CS-430 LESSON APPLIED. Three conditions, three answers, none borrowed.

    Absent, not-a-directory and refused all produce zero saves and all reported
    one identical sentence before this. Two of them were false: absence and a
    file-where-a-directory-should-be each SETTLE that there are no saves, and
    only a refusal leaves it open.
    """
    not_a_directory = pretend_account_dir / "World.sav"
    not_a_directory.write_bytes(save_bytes)
    refused = pretend_account_dir / "refused"
    refused.mkdir()
    refuse(monkeypatch, "iterdir", refused)

    absent = workdir._save_files(pretend_account_dir / "no-such-directory")  # noqa: SLF001
    a_file = workdir._save_files(not_a_directory)  # noqa: SLF001
    denied = workdir._save_files(refused)  # noqa: SLF001

    assert absent.problems[0].errno == errno.ENOENT
    assert a_file.problems[0].errno == errno.ENOTDIR
    assert denied.problems[0].errno == errno.EACCES
    # The two SETTLED errnos agree with each other, and neither agrees with the
    # one that settles nothing.
    assert absent.problems[0].detail == a_file.problems[0].detail
    assert denied.problems[0].detail != absent.problems[0].detail
    assert denied.problems[0].code != absent.problems[0].code


def test_a_directory_that_is_not_there_says_the_empty_result_is_the_whole_answer(
    tmp_path: Path,
) -> None:
    """THE CASE THAT FIRES ON EVERY MACHINE WITH NO GAME, so its sentence has to be true.

    Absence IS evidence that there are no saves. The report still arrives -
    nothing is dropped - but it says what absence means rather than borrowing
    the wording of a refusal.
    """
    listing = workdir._save_files(tmp_path / "no-such-directory")  # noqa: SLF001

    assert [problem.code for problem in listing.problems] == [workdir.LISTING_DIRECTORY_ABSENT]
    detail = listing.problems[0].detail
    assert "names no directory" in detail, detail
    assert "the whole answer" in detail, detail
    assert "not evidence" not in detail, detail
    assert listing.is_complete, "absence settles the question, so the empty result is trustworthy"


def test_a_path_that_is_a_file_says_the_same_as_one_that_is_not_there(
    pretend_account_dir: Path, save_bytes: bytes
) -> None:
    """A file is not a directory, so it holds no saves - and that is KNOWN, not feared.

    Shares the absent case's code deliberately: one sentence, "the path names no
    directory", is true of both, and inventing a third for a distinction no
    caller acts on would be sentences for their own sake.
    """
    not_a_directory = pretend_account_dir / "World.sav"
    not_a_directory.write_bytes(save_bytes)

    listing = workdir._save_files(not_a_directory)  # noqa: SLF001

    assert [problem.code for problem in listing.problems] == [workdir.LISTING_DIRECTORY_ABSENT]
    assert "not evidence" not in listing.problems[0].detail
    assert listing.is_complete


def test_a_directory_that_refuses_to_list_says_the_empty_result_is_not_evidence(
    pretend_account_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE ONLY CASE THE ORIGINAL SENTENCE WAS TRUE OF, and it had no test at all.

    A directory that is there and would not list may hold any number of saves.
    This is the one condition where an empty result proves nothing, and the one
    condition the first build's three tests never exercised.
    """
    refused = pretend_account_dir / "refused"
    refused.mkdir()
    refuse(monkeypatch, "iterdir", refused)

    listing = workdir._save_files(refused)  # noqa: SLF001

    assert [problem.code for problem in listing.problems] == [workdir.LISTING_DIRECTORY_UNREADABLE]
    detail = listing.problems[0].detail
    assert "not evidence" in detail, detail
    assert "leaves open" in detail, detail
    assert listing.problems[0].errno == errno.EACCES
    assert not listing.is_complete, "nothing was learned, so the empty result is not trustworthy"


def test_an_unrecognised_failure_is_reported_as_could_not_tell(
    pretend_account_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE DEFAULT LEANS THE SAFE WAY, which is the half a happy-path test misses.

    An errno this module has no reading of must not be classified as "nothing
    there" - that would license a caller to trust an empty result on the
    strength of a failure nobody has interpreted. Default to could-not-tell.
    """
    real = Path.iterdir
    target = pretend_account_dir / "strange"
    target.mkdir()

    def strange(self: Path, *args: object, **kwargs: object) -> object:
        if self == target:
            raise OSError(errno.EIO, "Input/output error", str(self))
        return real(self, *args, **kwargs)

    monkeypatch.setattr(Path, "iterdir", strange)

    listing = workdir._save_files(target)  # noqa: SLF001

    assert [problem.code for problem in listing.problems] == [workdir.LISTING_DIRECTORY_UNREADABLE]
    assert not listing.is_complete


def test_an_entry_that_cannot_be_classified_is_reported_rather_than_dropped(
    pretend_account_dir: Path, save_bytes: bytes
) -> None:
    """CS-438 proper. The entry still leaves the listing - but it no longer leaves quietly.

    The fault here is a broken symlink, whose ``stat()`` fails with ENOENT.
    ``Path.is_file()`` ignores that errno on every interpreter this project
    supports and answers False, so the old ``except OSError`` could not have
    caught THIS entry on any version - which is exactly why it vanished. That
    is a fact about ENOENT and NOT about every unreadable entry; see
    ``_save_files`` for what ``is_file()`` does with an errno pathlib does not
    ignore.
    """
    real = write_with_mtime(
        pretend_account_dir / "World.sav", save_bytes, 1_600_000_000_000_000_000
    )
    make_broken_symlink(pretend_account_dir / "Unreadable.sav")

    listing = workdir._save_files(pretend_account_dir)  # noqa: SLF001

    assert listing.saves == (real,), "the readable save must still be listed"
    assert [problem.code for problem in listing.problems] == [workdir.LISTING_ENTRY_ABSENT]


def test_an_entry_that_vanished_and_one_that_refused_do_not_report_the_same_thing(
    pretend_account_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE SIBLING OF THE DIRECTORY SPLIT, same root cause, found by the same grep.

    A broken symlink names no file, so it is KNOWABLY not a save. An entry that
    refused to stat might be one. Folding both into "whether it is a save is
    unknown" is the same over-claim as the directory case, one level down.
    """
    make_broken_symlink(pretend_account_dir / "Vanished.sav")
    denied_entry = pretend_account_dir / "Denied.sav"
    denied_entry.write_bytes(b"x")
    refuse(monkeypatch, "stat", denied_entry)

    listing = workdir._save_files(pretend_account_dir)  # noqa: SLF001

    vanished = only_with_errno(listing, errno.ENOENT)
    denied = only_with_errno(listing, errno.EACCES)
    assert vanished.code == workdir.LISTING_ENTRY_ABSENT
    assert denied.code == workdir.LISTING_ENTRY_UNREADABLE
    assert "names no file" in vanished.detail, vanished.detail
    assert "unknown" not in vanished.detail, vanished.detail
    assert "unknown" in denied.detail, denied.detail
    assert not listing.is_complete, "the refused entry might have been a save"


def test_the_entry_report_is_true_of_every_entry_that_can_raise_it(
    pretend_account_dir: Path,
) -> None:
    """THE SENTENCE IS CHECKED, not merely the firing (the CS-430 lesson).

    Both entry details say the entry was NAMED AS A SAVE. That is only true
    because the suffix test short-circuits ahead of the stat, so an unstattable
    entry named anything else is never reached and never reported. Both halves
    are asserted here; without the second, the sentence would be a guess about
    the input.
    """
    make_broken_symlink(pretend_account_dir / "notes.txt")

    other_suffix = workdir._save_files(pretend_account_dir)  # noqa: SLF001
    assert other_suffix.problems == (), (
        "an entry NOT named as a save reached the classification step, so the report's "
        "sentence is not true of everything that can raise it"
    )

    make_broken_symlink(pretend_account_dir / "Unreadable.sav")
    named_as_a_save = workdir._save_files(pretend_account_dir)  # noqa: SLF001

    assert len(named_as_a_save.problems) == EXPECT_AT_LEAST_ONE
    detail = named_as_a_save.problems[0].detail
    assert "named as a save" in detail, detail
    assert "absent from this listing" in detail, detail


@pytest.mark.parametrize(
    ("condition", "trusted"),
    [
        ("clean", True),
        ("directory-absent", True),
        ("directory-not-a-directory", True),
        ("directory-refused", False),
        ("entry-vanished", True),
        ("entry-refused", False),
    ],
)
def test_is_complete_says_whether_an_empty_result_can_be_trusted(
    condition: str,
    trusted: bool,
    pretend_account_dir: Path,
    save_bytes: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ONE BOOLEAN, ONE MEANING, GRADED ON EVERY CONDITION THAT CAN PRODUCE IT.

    ``is_complete`` is the absence of an INCONCLUSIVE problem, not the absence
    of every problem. A directory that is not there reports itself AND answers
    True, because "no such directory" and "no saves in it" are one fact. Only a
    condition that left the question open answers False.
    """
    target = pretend_account_dir
    if condition == "directory-absent":
        target = pretend_account_dir / "no-such-directory"
    elif condition == "directory-not-a-directory":
        target = pretend_account_dir / "World.sav"
        target.write_bytes(save_bytes)
    elif condition == "directory-refused":
        target = pretend_account_dir / "refused"
        target.mkdir()
        refuse(monkeypatch, "iterdir", target)
    elif condition == "entry-vanished":
        make_broken_symlink(pretend_account_dir / "Vanished.sav")
    elif condition == "entry-refused":
        denied = pretend_account_dir / "Denied.sav"
        denied.write_bytes(b"x")
        refuse(monkeypatch, "stat", denied)

    listing = workdir._save_files(target)  # noqa: SLF001

    assert listing.saves == (), "this parametrisation is about the EMPTY result"
    assert listing.is_complete is trusted
    if condition != "clean":
        assert listing.problems, "every condition here reports, whether or not it is complete"


def test_latest_save_hands_the_listing_problems_to_a_caller_that_asks(
    pretend_account_dir: Path, save_bytes: bytes
) -> None:
    """The report reaches the public surface, and the return value is unchanged.

    ``latest_save`` still answers None for a directory it could not read, and
    still does not raise for one - the report is what is added, not a new
    failure mode.
    """
    not_a_directory = pretend_account_dir / "World.sav"
    not_a_directory.write_bytes(save_bytes)
    problems: list[workdir.ListingProblem] = []

    assert workdir.latest_save(not_a_directory, problems=problems) is None
    assert [problem.code for problem in problems] == [workdir.LISTING_DIRECTORY_ABSENT]


def test_latest_save_tells_a_directory_that_is_not_there_from_one_that_refused(
    pretend_account_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE DOCSTRING'S PROMISE, GRADED. It used to promise a distinction it did not make.

    ``latest_save``'s ``problems`` argument is documented as the way a caller
    tells a machine with no game from a directory that refused to list. Both
    still return None; the CODES are what differ, and before this they did not.
    """
    refused = pretend_account_dir / "refused"
    refused.mkdir()
    refuse(monkeypatch, "iterdir", refused)
    absent_problems: list[workdir.ListingProblem] = []
    refused_problems: list[workdir.ListingProblem] = []

    assert workdir.latest_save(pretend_account_dir / "gone", problems=absent_problems) is None
    assert workdir.latest_save(refused, problems=refused_problems) is None

    assert [problem.code for problem in absent_problems] == [workdir.LISTING_DIRECTORY_ABSENT]
    assert [problem.code for problem in refused_problems] == [workdir.LISTING_DIRECTORY_UNREADABLE]


def test_latest_save_reports_nothing_for_a_directory_it_could_read(
    pretend_account_dir: Path, save_bytes: bytes
) -> None:
    """NON-VACUITY for the sink above, and the default stays a plain call."""
    newest = write_with_mtime(
        pretend_account_dir / "World.sav", save_bytes, 1_600_000_000_000_000_000
    )
    problems: list[workdir.ListingProblem] = []

    assert workdir.latest_save(pretend_account_dir, problems=problems) == newest
    assert problems == []
    # The sink is optional; every existing caller passes nothing.
    assert workdir.latest_save(pretend_account_dir) == newest


# ---------------------------------------------------------------------------
# 4c. What is_file() hides, and what this module therefore may not claim
# ---------------------------------------------------------------------------
#
# THE FIRST BUILD SHIPPED A FALSE REACHABILITY CLAIM, in this file and in
# ``_save_files``: that the ORIGINAL ``except OSError`` around ``is_file()`` was
# unreachable because ``is_file()`` swallows everything. That is true on this
# machine's interpreter and NOT true on the floor this project declares in
# pyproject.toml and scripts/verify_env.py, where ``Path`` inherits
# ``PathBase.is_file`` and re-raises any errno outside pathlib's ignored set.
# Established from the CPython source for that branch, NOT executed - no such
# interpreter is installed here - and corroborated by executing the same shape
# on the older interpreter that IS installed.
#
# What survives is narrower and is what the test below asserts: the ENOENT of a
# broken symlink is ignored on every supported version, so the fixture case
# really was invisible to the old handler. That is a fact about ENOENT, not a
# universal about unreadable entries.


def test_stat_reports_the_broken_symlink_fault_that_is_file_hides(
    pretend_account_dir: Path,
) -> None:
    """THE MECHANISM THE CLASSIFICATION RESTS ON, executed rather than asserted about.

    ``stat()`` raises where ``is_file()`` answers a bare False. That difference
    is the whole reason the scan reads the mode directly, and it is checked
    here against the interpreter actually running rather than against a
    sentence about interpreters.
    """
    link = make_broken_symlink(pretend_account_dir / "Unreadable.sav")

    with pytest.raises(FileNotFoundError) as caught:
        link.stat()

    assert caught.value.errno == errno.ENOENT, (
        "the broken-symlink fixture stopped producing ENOENT, so the narrow claim in "
        "_save_files about which errno is ignored has to be re-derived"
    )
    assert link.is_file() is False, "is_file() let an exception out for an IGNORED errno"


def test_the_save_listing_does_not_claim_an_unreadable_entry_raises_nothing() -> None:
    """THE REFUTED SENTENCE, asserted absent rather than reworded.

    "there is no exception to catch" was a universal, and the floor interpreter
    refutes it. ADR 0008 forecloses hedging a refuted claim into "believed to
    be" - the hedge has the same falsification surface and reads as evidence -
    so this grades the absence of the clause, not its softening.
    """
    doc = workdir._save_files.__doc__ or ""  # noqa: SLF001

    assert "there is no exception to catch" not in doc
    assert "indistinguishable" not in doc, (
        "the sentence claiming is_file() cannot distinguish an unreadable entry is back"
    )
    # NON-VACUITY: the paragraph that replaced it is still there to be read.
    assert "varies across the interpreter range" in doc


# ---------------------------------------------------------------------------
# 4d. The redaction boundary, tested where it actually is
# ---------------------------------------------------------------------------
#
# WHY THESE EXIST. ``_listing_problem`` takes the exception as a PARAMETER
# rather than catching it, so it sits outside every ``except ... as NAME`` body
# and is a redaction BOUNDARY in its own right - the place where an object
# carrying a path is turned into fields that carry none. A boundary is tested
# at the boundary.
#
# The precedent is ``safe_exc_text``, the same shape one layer over: it renders
# its own argument, and it carries dedicated redaction tests in
# tests/test_precommit_gate.py rather than being covered incidentally. These
# are that, for this helper.
#
# NO CLAIM IS MADE HERE ABOUT WHICH OTHER TEST DOES OR DOES NOT CATCH A LEAK IN
# THIS FUNCTION. A sentence of that shape is a detection claim, and ADR 0008
# says a detection claim is derived by the suite or deleted - never written -
# because it is falsified by any change anywhere, including a change that
# widens some other sweep to reach this. The tests below are the guard; they do
# not describe one.

#: Leak bait. Shaped like the things a real OSError from this scan would carry
#: - a directory segment, a platform account id and a world name - and none of
#: them is real. Deliberately NOT rooted under a user profile: an absolute home
#: path in a tracked file is refused outright by
#: ``test_no_absolute_home_paths_in_authored_files``, fictional account name or
#: not, and that guard is right. What these tests need is separators and
#: identifier-shaped segments, which a non-home root supplies just as well.
_BAIT_WORLD = "BaitWorldName"
_BAIT_SEGMENT = "BaitDirectory"
_BAIT_PATH = f"Z:\\{_BAIT_SEGMENT}\\{PRETEND_ACCOUNT}\\{_BAIT_WORLD}_010101-020202.sav"


def problem_surfaces(problem: workdir.ListingProblem) -> str:
    """Every way this object can reach a log line, a message or a repr, joined."""
    return str(problem) + repr(problem) + problem.code + problem.detail + str(problem.errno)


def test_the_problem_builder_copies_no_field_of_the_exception_but_the_errno() -> None:
    """The boundary itself, called directly, with the path in every field it has.

    ``filename``, ``strerror``, ``args`` and ``str()`` all carry the path on a
    real OSError from this scan. Only the errno may cross.
    """
    exc = PermissionError(errno.EACCES, f"Permission denied: {_BAIT_PATH}", _BAIT_PATH)

    problem = workdir._listing_problem(  # noqa: SLF001
        workdir.LISTING_ENTRY_ABSENT, workdir.LISTING_ENTRY_UNREADABLE, exc
    )
    surfaces = problem_surfaces(problem)

    assert _BAIT_WORLD not in surfaces, "the world name reached the report"
    assert PRETEND_ACCOUNT not in surfaces, "the account id reached the report"
    assert _BAIT_PATH not in surfaces
    assert _BAIT_SEGMENT not in surfaces, "a directory segment reached the report"
    assert "\\" not in surfaces, "a path separator reached the report"
    assert "/" not in surfaces, "a path separator reached the report"
    assert ".sav" not in surfaces, "a filename reached the report"
    assert problem.errno == errno.EACCES, "the one field that MAY cross did not"


def test_the_problem_builder_answers_a_detail_from_the_table_and_not_from_the_exception() -> None:
    """The detail is keyed by CODE, so no input can steer it into rendering anything.

    Two exceptions differing in every string they carry produce the identical
    detail, which is what "fixed line, keyed by code" means operationally.
    """
    one = PermissionError(errno.EACCES, f"Permission denied: {_BAIT_PATH}", _BAIT_PATH)
    two = PermissionError(errno.EACCES, "denied", "elsewhere.sav")

    first = workdir._listing_problem(  # noqa: SLF001
        workdir.LISTING_DIRECTORY_ABSENT, workdir.LISTING_DIRECTORY_UNREADABLE, one
    )
    second = workdir._listing_problem(  # noqa: SLF001
        workdir.LISTING_DIRECTORY_ABSENT, workdir.LISTING_DIRECTORY_UNREADABLE, two
    )

    assert first == second
    assert first.detail in workdir._LISTING_DETAILS.values()  # noqa: SLF001


def test_the_problem_builder_picks_the_settled_code_only_for_a_settled_errno() -> None:
    """The classification, exercised at the boundary rather than only through a scan.

    Every errno the scan can meet is graded here, including one carrying no
    errno at all - which must not be read as "nothing there".
    """
    settled = workdir.LISTING_DIRECTORY_ABSENT
    open_question = workdir.LISTING_DIRECTORY_UNREADABLE

    def code_for(exc: OSError) -> str:
        return workdir._listing_problem(settled, open_question, exc).code  # noqa: SLF001

    assert code_for(FileNotFoundError(errno.ENOENT, "nope", "x")) == settled
    assert code_for(NotADirectoryError(errno.ENOTDIR, "nope", "x")) == settled
    assert code_for(PermissionError(errno.EACCES, "nope", "x")) == open_question
    assert code_for(OSError(errno.EIO, "nope", "x")) == open_question
    assert code_for(OSError()) == open_question, (
        "an exception carrying no errno was read as 'nothing there', which would let a "
        "caller trust an empty result on the strength of a failure nobody classified"
    )


def test_the_problem_builder_carries_no_errno_through_as_none() -> None:
    """An OSError without an errno is reported, not crashed on."""
    problem = workdir._listing_problem(  # noqa: SLF001
        workdir.LISTING_ENTRY_ABSENT, workdir.LISTING_ENTRY_UNREADABLE, OSError()
    )

    assert problem.errno is None
    assert problem.code == workdir.LISTING_ENTRY_UNREADABLE
    assert problem.detail


def test_every_listing_code_has_a_detail_and_every_detail_a_code() -> None:
    """No code can ship without a sentence, and no sentence without a code.

    A missing entry in the table is a ``KeyError`` at the exact moment the scan
    is trying not to fail, which is the worst possible time for one.
    """
    codes = {
        workdir.LISTING_DIRECTORY_ABSENT,
        workdir.LISTING_DIRECTORY_UNREADABLE,
        workdir.LISTING_ENTRY_ABSENT,
        workdir.LISTING_ENTRY_UNREADABLE,
    }

    assert set(workdir._LISTING_DETAILS) == codes  # noqa: SLF001
    assert len({*workdir._LISTING_DETAILS.values()}) == len(codes), (  # noqa: SLF001
        "two codes share one sentence, so at least one of them is described by a line "
        "written for a different condition - the CS-430 shape"
    )
    assert codes > workdir._INCONCLUSIVE_CODES  # noqa: SLF001


def test_the_listing_report_carries_no_path_no_name_and_no_exception_text(
    pretend_account_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PRIVACY END TO END. A save's filename carries the world name, its directory the id.

    The helper above is tested directly; this proves the whole scan reaches it
    rather than building a report some other way. Both entry paths are covered
    - the real broken symlink and the injected refusal - because they are two
    different ``except`` sites.
    """
    make_broken_symlink(pretend_account_dir / "SecretWorldName.sav")
    denied = pretend_account_dir / "OtherSecretName.sav"
    denied.write_bytes(b"x")
    refuse(monkeypatch, "stat", denied)

    listing = workdir._save_files(pretend_account_dir)  # noqa: SLF001
    surfaces = "".join(problem_surfaces(problem) for problem in listing.problems)

    expected_problems = 2
    assert len(listing.problems) == expected_problems, "nothing was rendered; this proves nothing"
    assert "SecretWorldName" not in surfaces, "the report leaks the entry name"
    assert "OtherSecretName" not in surfaces, "the report leaks the entry name"
    assert PRETEND_ACCOUNT not in surfaces, "the report leaks the account directory"
    assert str(pretend_account_dir) not in surfaces
    assert "\\" not in surfaces, "a path reached the report"
    assert "/" not in surfaces, "a path reached the report"


# ===========================================================================
# 5. purge_work_dir removes only what this module created
# ===========================================================================


def test_purge_removes_the_copies_this_module_made(pretend_source: Path, work: Path) -> None:
    """The copies go, and the count returned is the number actually removed."""
    workdir.copy_for_read(pretend_source, work_root=work)

    removed = workdir.purge_work_dir(work_root=work)

    assert removed == EXPECT_AT_LEAST_ONE, "purge did not report the copy it removed"
    assert workdir.purge_work_dir(work_root=work) == EXPECT_NONE, "purge is not idempotent"


def test_purge_removes_only_this_modules_copies(pretend_source: Path, work: Path) -> None:
    """An unrelated file planted in the work root SURVIVES.

    Two independent conditions have to hold for a file to be removed - it lives
    in the module's own copies directory AND it carries the module's suffix -
    so this plants a file that fails each condition separately. A purge keyed
    on the directory alone would delete the second one.
    """
    copy = workdir.copy_for_read(pretend_source, work_root=work)

    bystander = work / "operator-notes.txt"
    bystander.write_bytes(b"not ours")
    neighbour = copy.parent / "operator-notes.txt"
    neighbour.write_bytes(b"not ours either")

    removed = workdir.purge_work_dir(work_root=work)

    assert removed == EXPECT_AT_LEAST_ONE
    assert not copy.exists(), "purge left the copy behind"
    assert bystander.is_file(), "purge deleted an unrelated file in the work root"
    assert neighbour.is_file(), "purge deleted an unrelated file in the copies directory"


def test_purge_leaves_a_subdirectory_alone(pretend_source: Path, work: Path) -> None:
    """A directory is never removed, only files this module wrote."""
    workdir.copy_for_read(pretend_source, work_root=work)
    nested = work / "operator-scratch"
    nested.mkdir()

    workdir.purge_work_dir(work_root=work)

    assert nested.is_dir(), "purge removed a directory it did not create"


def test_purge_of_an_absent_work_root_is_zero_not_an_error(tmp_path: Path) -> None:
    """Nothing to purge is zero, not an exception and not a created directory."""
    absent = tmp_path / "never-created"

    assert workdir.purge_work_dir(work_root=absent) == EXPECT_NONE
    assert not absent.exists(), "purge created the work root it was asked to empty"


# ===========================================================================
# work_root itself
# ===========================================================================


def test_work_root_defaults_to_work_under_the_repo_root() -> None:
    """The default is <repo>/work, derived from the module's own location."""
    root = workdir.work_root()

    assert root.name == "work"
    assert root.parent == REPO_ROOT, "the default work root is not under the repo root"


def test_work_root_is_environment_overridable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The override is a CLOCKSPEED_-prefixed environment name, as the rest of the layer is."""
    assert workdir.ENV_WORK_ROOT.startswith("CLOCKSPEED_")
    monkeypatch.setenv(workdir.ENV_WORK_ROOT, str(tmp_path / "elsewhere"))

    assert workdir.work_root() == tmp_path / "elsewhere"


def test_work_root_does_not_create_anything() -> None:
    """Asking where the work root is must not make one.

    ``work_root()`` is a question. A resolver with a side effect would create a
    directory in the repo on any machine that merely imported the module and
    asked, including a machine with no game and no save.
    """
    root = workdir.work_root()
    existed = root.exists()

    workdir.work_root()

    assert root.exists() == existed, "work_root() created the directory it reports"


def test_the_default_work_root_is_gitignored() -> None:
    """/work/ must stay ignored: the copies are real saves and carry PII.

    Asked of git rather than asserted against the text of .gitignore, because
    what matters is the effective ignore decision and not the presence of a
    line. SKIPS WITH A REASON when git is unavailable.
    """
    probe = workdir.work_root() / "SyntheticWorld.sav"
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(probe)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=_CHILD_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        pytest.skip(f"git is not usable here: {type(exc).__name__}")

    ignored = result.returncode
    assert ignored == 0, (
        "the default work root is NOT gitignored. The copies under it are real saves and "
        "carry the platform account id and the player display name."
    )


# ===========================================================================
# 6. The no-write proof, in a child interpreter
# ===========================================================================

# Installs a RECORDING audit hook BEFORE importing the module under test, runs
# one copy, then classifies what the interpreter actually did.
#
# A recording spy rather than a raising one, deliberately: a hook that raised on
# the first write-intent event would abort the run at the first finding and
# report one violation where there may be several, and an exception raised
# inside an audit hook unwinds through whatever code triggered it, which makes
# the traceback a story about the hook rather than about the write.
#
# The child emits COUNTS AND EVENT NAMES ONLY, never a path. The pretend save
# root lives under the temporary directory, whose Windows 8.3 rendering spells
# the operator's account name as six characters plus a tilde and a digit
# (clockspeed/data/locate.py documents that exact leak), so printing the paths
# it classified would put an account name in the CI log.
_PROBE_NO_WRITE = """
import json
import os
import sys
from pathlib import Path

SAVE_ROOT, SOURCE, WORK = sys.argv[1], sys.argv[2], sys.argv[3]

WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
WRITE_MODE_CHARS = frozenset("wax+")

MUTATING = frozenset({
    "os.rename", "os.replace", "os.remove", "os.unlink", "os.mkdir", "os.rmdir",
    "os.truncate", "os.chmod", "os.chown", "os.utime", "os.link", "os.symlink",
    "os.setxattr", "os.removexattr", "shutil.copyfile", "shutil.copymode",
    "shutil.copystat", "shutil.move", "shutil.rmtree", "shutil.unpack_archive",
})

RECORDS = []
RECORDING = [True]


def texts(args):
    out = []
    for item in args:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, bytes):
            out.append(item.decode("utf-8", "replace"))
        elif isinstance(item, os.PathLike):
            out.append(os.fspath(item))
    return out


def hook(event, args):
    if not RECORDING[0]:
        return
    if event == "open":
        mode = args[1] if len(args) > 1 and isinstance(args[1], str) else ""
        flags = args[2] if len(args) > 2 and isinstance(args[2], int) else 0
        RECORDS.append(("open", texts(args[:1]), mode, flags))
    elif event in MUTATING:
        RECORDS.append((event, texts(args), "", 0))


sys.addaudithook(hook)

from clockspeed.save import workdir

copy = workdir.copy_for_read(Path(SOURCE), work_root=Path(WORK))

# Stop recording BEFORE classifying: resolve() below raises its own events, and
# a list being appended to while it is iterated is a different bug entirely.
RECORDING[0] = False

root = Path(SAVE_ROOT).resolve()


def under_save_root(text):
    try:
        return Path(text).resolve().is_relative_to(root)
    except (OSError, ValueError):
        return False


write_intent = 0
mutating = 0
read_opens = 0
offenders = []

for event, paths, mode, flags in RECORDS:
    if not any(under_save_root(p) for p in paths):
        continue
    if event == "open":
        if (WRITE_MODE_CHARS & set(mode)) or (flags & WRITE_FLAGS):
            write_intent += 1
            offenders.append("open(mode=" + mode + ")")
        else:
            read_opens += 1
    else:
        mutating += 1
        offenders.append(event)

print(json.dumps({
    "write_intent_under_save_root": write_intent,
    "mutating_under_save_root": mutating,
    "read_opens_under_save_root": read_opens,
    "offending_event_names": sorted(set(offenders)),
    "events_seen": len(RECORDS),
    "copy_exists": copy.is_file(),
    "copy_under_work": copy.resolve().is_relative_to(Path(WORK).resolve()),
}))
"""


def run_child(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run a child interpreter from the repo root and capture its output.

    ``sys.executable`` is the only correct way to name the interpreter: a bare
    name would resolve off PATH to whatever happens to be first, and an
    absolute interpreter path in a tracked file is forbidden outright.

    Callers bind ``returncode`` to a local before asserting on it. That is not
    style - asserting on the CompletedProcess makes pytest repr ``args[0]``,
    the absolute interpreter path, which on a default install sits under the
    operator's home directory and carries their account name into the log. The
    same discipline is recorded at tests/data/test_phase2_gate.py::run_child.
    """
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=_CHILD_TIMEOUT_SECONDS,
        env=env,
        check=False,
    )


def isolated_env(**overrides: str) -> dict[str, str]:
    """A child environment with every resolver pointed at nothing, then overridden."""
    env = dict(os.environ)
    env[ENV_GAME_DIR] = str(ABSENT / "install")
    env[ENV_SAVE_ROOT] = str(ABSENT / "saves")
    env[ENV_ACCOUNT_DIR] = str(ABSENT / "account")
    env[ENV_LOCAL_CONFIG] = str(ABSENT / "local.json")
    env.pop(workdir.ENV_WORK_ROOT, None)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env.update(overrides)
    return env


def test_no_write_intent_event_reaches_the_save_root(
    pretend_source: Path, pretend_save_root: Path, work: Path
) -> None:
    """The interpreter's own audit stream says the save root was only ever read.

    Three assertions, and the third is the one that gives the other two their
    meaning. "No writes happened" is trivially true of a function that never
    ran, so the count of READ opens under the pretend save root is asserted
    non-zero in the same test. Without it this passes against a ``copy_for_read``
    whose body is ``pass``.
    """
    env = isolated_env(**{ENV_SAVE_ROOT: str(pretend_save_root)})
    child = run_child(
        ["-c", _PROBE_NO_WRITE, str(pretend_save_root), str(pretend_source), str(work)], env
    )

    exit_code = child.returncode
    assert exit_code == 0, (
        f"the audit probe failed:\nstdout:\n{child.stdout}\nstderr:\n{child.stderr}"
    )

    report = json.loads(child.stdout)
    write_intent = report["write_intent_under_save_root"]
    mutating = report["mutating_under_save_root"]
    read_opens = report["read_opens_under_save_root"]
    offenders = report["offending_event_names"]

    assert write_intent == EXPECT_NONE, (
        f"{write_intent} write-intent open(s) targeted the save root: {offenders}"
    )
    assert mutating == EXPECT_NONE, (
        f"{mutating} mutating event(s) targeted the save root: {offenders}"
    )
    assert read_opens >= EXPECT_AT_LEAST_ONE, (
        "no read open under the save root was recorded, so this test proves nothing - "
        "copy_for_read did not read the source at all"
    )
    assert report["copy_exists"] is True
    assert report["copy_under_work"] is True


def test_the_audit_probe_can_actually_see_a_write(
    pretend_source: Path, pretend_save_root: Path, work: Path
) -> None:
    """The detector is proven to detect, on a deliberate write into the save root.

    A guard is a claim until it has been shown failing. This runs the same
    classification over a child that DOES write into the pretend save root and
    asserts the count comes back non-zero - so a hook that silently stopped
    recording, or a mask that matched nothing, turns this red instead of
    leaving the test above passing for the wrong reason.
    """
    culprit = _PROBE_NO_WRITE.replace(
        "copy = workdir.copy_for_read(Path(SOURCE), work_root=Path(WORK))",
        "copy = workdir.copy_for_read(Path(SOURCE), work_root=Path(WORK))\n"
        "(Path(SAVE_ROOT) / 'deliberate.tmp').write_bytes(b'x')",
    )
    assert culprit != _PROBE_NO_WRITE, "the probe source changed and this self-test is stale"

    env = isolated_env(**{ENV_SAVE_ROOT: str(pretend_save_root)})
    child = run_child(
        ["-c", culprit, str(pretend_save_root), str(pretend_source), str(work / "b")], env
    )

    exit_code = child.returncode
    assert exit_code == 0, f"the self-test probe failed:\n{child.stdout}\n{child.stderr}"

    report = json.loads(child.stdout)
    write_intent = report["write_intent_under_save_root"]
    assert write_intent >= EXPECT_AT_LEAST_ONE, (
        "the audit probe did not notice a deliberate write into the save root, "
        "so it cannot be trusted to notice an accidental one"
    )


# ===========================================================================
# 7. The whole suite, with no install and no save
# ===========================================================================

_RECURSING_TEST = "test_the_workdir_suite_passes_with_no_install_and_no_save"

# A pytest NODE ID, which is not a path: it is relative to the rootdir and uses
# forward slashes on every platform. Measured, after the absolute-Windows-path
# form silently matched nothing - `--deselect` accepts an id it cannot find
# without a word of complaint, the child then ran the recursing test, and that
# spawned a subprocess chain that only stopped at the timeout.
# ``test_the_child_run_deselects_only_the_recursing_test`` is what caught it,
# which is the whole reason that test exists.
_MODULE_NODE_ID = THIS_MODULE.relative_to(REPO_ROOT).as_posix()


def _child_pytest_args() -> list[str]:
    """Run this module in a child, minus the one test that would recurse."""
    return [
        "-m",
        "pytest",
        _MODULE_NODE_ID,
        f"--deselect={_MODULE_NODE_ID}::{_RECURSING_TEST}",
        "-p",
        "no:cacheprovider",
        "-q",
    ]


def test_the_workdir_suite_passes_with_no_install_and_no_save() -> None:
    """This module exits zero with all four overrides pointed at a nonexistent path.

    The rule suite has to run on a machine that has never had the game on it.
    A test here that reached for the real save root, the real install or the
    operator's config/local.json turns this red on the machine where the game
    IS installed - the only machine where the mistake is otherwise invisible.
    """
    child = run_child(_child_pytest_args(), isolated_env())

    exit_code = child.returncode
    assert exit_code == 0, (
        "the workdir suite does not pass without an install or a save.\n"
        f"exit code: {exit_code}\nstdout:\n{child.stdout}\nstderr:\n{child.stderr}"
    )
    passed = re.search(r"(\d+) passed", child.stdout)
    assert passed is not None, f"the child run reported no passing tests:\n{child.stdout}"
    assert int(passed.group(1)) >= EXPECT_AT_LEAST_ONE


def test_the_child_run_deselects_only_the_recursing_test() -> None:
    """The recursion guard is verified against pytest's own collection, not assumed.

    ``--deselect`` silently accepts a node id it does not match, so "the guard
    works" is a claim until pytest is asked what it collected. Both halves
    matter: the recursing test absent, and the rest of this module present. A
    guard that deselected everything would also make the test above pass.
    """
    # NOT a second -q. Two of them collapse --collect-only to a bare count,
    # and a count contains no test name, so every assertion below would be
    # asserting against an empty haystack.
    child = run_child([*_child_pytest_args(), "--collect-only"], isolated_env())

    exit_code = child.returncode
    assert exit_code == 0, f"collection failed:\n{child.stdout}\n{child.stderr}"

    collected = child.stdout
    assert _RECURSING_TEST not in collected, "the child collects the recursing test"
    for sibling in (
        "test_the_copy_is_byte_identical_to_the_source",
        "test_the_source_is_untouched_by_the_copy",
        "test_purge_removes_only_this_modules_copies",
    ):
        assert sibling in collected, (
            f"the child run collects no {sibling}; the deselect is too wide and the gate "
            "would pass by testing nothing"
        )


# ===========================================================================
# The single-writer commitment (docs/adr/0007 Decision item 6)
# ===========================================================================


def test_workdir_is_the_only_save_module_that_can_write() -> None:
    """No sibling in clockspeed/save/ opens a file for write.

    docs/adr/0007 Decision item 6 states this as a COMMITMENT that a later gate
    converts into a static assertion. This is the narrow, local form of it: a
    text scan of the sibling modules for a write-capable open. It is not the
    AST gate that item promises and does not claim to be - it is the check that
    keeps the property true between now and then.
    """
    package = REPO_ROOT / "clockspeed" / "save"

    offenders = {
        module.name: modes
        for module in sorted(package.glob("*.py"))
        if module.name != "workdir.py"
        and (modes := write_modes_in(module.read_text(encoding="utf-8")))
    }

    assert offenders == {}, (
        "these save modules open a file for write, but workdir.py owns the only write "
        f"in the package: {offenders}"
    )


def test_the_single_writer_detector_actually_detects() -> None:
    """The detector above is shown finding a write, so a green result means something.

    The last two cases are the false positive the naive form of this check has:
    a read open whose FILENAME happens to contain a mode character.
    """
    assert write_modes_in('with path.open("wb") as fh:') == ["wb"]
    assert write_modes_in("with path.open('a') as fh:") == ["a"]
    assert write_modes_in('with open(target, "w+") as fh:') == ["w+"]
    assert write_modes_in('with path.open("rb") as fh:') == []
    assert write_modes_in('with open("data.txt") as fh:') == []
    assert write_modes_in('with open(path, "rb") as fh:') == []


# ---------------------------------------------------------------------------
# CS-471 - THIS MODULE'S LIBRARY REACH, DECLARED.
#
# The guard is owned by ``reach_guard`` and applied across this package by
# the suite-wide test in ``test_reach_guard``, which walks the package
# directory rather than waiting to be called. Before CS-471 this module touched a library
# primitive while declaring no reach at all, and the suite had no check that
# would say so.
#
# The wording here is deliberately free of the CS-420 quantifier vocabulary,
# because two modules carrying this block sit inside that fence.
# ---------------------------------------------------------------------------

#: Helpers that genuinely reach the save library, name to why each reaches.
_GRADED_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType({})

#: Touches a primitive WITHOUT consuming a real save path, name to why.
#: Asserted still reaching, so a stale exemption reddens the guard.
_EXEMPT_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType(
    {
        reach_guard.MODULE_SCOPE_REACH: (
            "Path(__file__).resolve() at module scope, building this repo's "
            "own root and this module's own path as constants. It resolves a "
            "tracked source file, never a save directory and never the "
            "account directory"
        ),
        "sha256_of": ("digests a file the caller wrote into tmp_path "),
        "stat_triple": ("stats a file the caller wrote into tmp_path "),
        "test_an_unrecognised_failure_is_reported_as_could_not_tell": (
            "takes a reference to Path.iterdir in order to REPLACE it, and its "
            "stand-in delegates to that reference for every path except the one "
            "it fakes a failure on. A primitive named to be BROKEN rather than "
            "used is the inversion this guard's keying note records, and it "
            "surfaces here because CS-491 widened the alias expansion into "
            "function locals - a local holding the real method is "
            "indistinguishable BY NAME from one holding a reach. WHAT IT LISTS, "
            "corrected: not pretend_account_dir but a child directory the test "
            "creates under it and then makes unreadable, so the stand-in raises "
            "for that path rather than delegating and NOTHING is listed at all. "
            "The containment is transitive - the child sits under "
            "pretend_account_dir, which is built under tmp_path - and the first "
            "reading of this reason described work the test does not do "
        ),
        "test_latest_save_hands_the_listing_problems_to_a_caller_that_asks": (
            "applies the locator to a pytest tmp_path standing in for a "
            "save root, never to the real one "
        ),
        "test_latest_save_ignores_files_that_are_not_saves": (
            "applies the locator to a pytest tmp_path standing in for a "
            "save root, never to the real one "
        ),
        "test_latest_save_is_stable_across_two_runs": (
            "applies the locator to a pytest tmp_path standing in for a "
            "save root, never to the real one "
        ),
        "test_latest_save_picks_a_manual_save_when_it_is_the_newest": (
            "applies the locator to a pytest tmp_path standing in for a "
            "save root, never to the real one "
        ),
        "test_latest_save_picks_the_newest_across_manual_saves_and_autosaves": (
            "applies the locator to a pytest tmp_path standing in for a "
            "save root, never to the real one "
        ),
        "test_latest_save_reports_nothing_for_a_directory_it_could_read": (
            "applies the locator to a pytest tmp_path standing in for a "
            "save root, never to the real one "
        ),
        "test_latest_save_returns_none_for_an_absent_directory": (
            "applies the locator to a pytest tmp_path standing in for a "
            "save root, never to the real one "
        ),
        "test_latest_save_returns_none_for_an_empty_directory": (
            "applies the locator to a pytest tmp_path standing in for a "
            "save root, never to the real one "
        ),
        "test_latest_save_returns_none_when_nothing_resolves": (
            "passes NO path at all - it asserts the locator declines when "
            "nothing resolves. Its containment is the autouse fixture in "
            "this module, which points the CLOCKSPEED environment variables "
            "at a directory under the repo that does not exist. MEASURED, "
            "so the distinction is not academic: the same call with that "
            "fixture absent resolves a real save on this machine "
        ),
        "test_latest_save_tells_a_directory_that_is_not_there_from_one_that_refused": (
            "applies the locator to a pytest tmp_path standing in for a "
            "save root, never to the real one "
        ),
        "test_stat_reports_the_broken_symlink_fault_that_is_file_hides": (
            "stats a broken symlink this test created in tmp_path "
        ),
        "test_the_copy_is_byte_identical_to_the_source": (
            "resolves tmp_path work and source roots this test created "
        ),
        "test_the_copy_survives_a_body_with_every_byte_value": (
            "reads back a synthetic body this test wrote into tmp_path "
        ),
        "test_workdir_is_the_only_save_module_that_can_write": (
            "globs THIS REPO's own clockspeed/save sources to prove no "
            "other module can write, never a save directory "
        ),
    }
)
