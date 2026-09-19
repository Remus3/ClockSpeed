"""CS-1156 - a credential must not survive a rendered failure report.

THE DEFECT, MEASURED RATHER THAN REASONED ABOUT. On 2026-09-19 a suite run
failed on an unrelated `FileNotFoundError` inside `tests/test_pre_push_ref_race.py`,
and pytest rendered the frame it crashed in. That frame was a
``subprocess.run(..., env=...)`` call, so the rendered arguments were the WHOLE
environment dict - and this machine's environment carries an `sk-ant-` prefixed
admin key. The key printed in full, beside a home path the shipped redactor DID
replace, which is what makes the surviving credential look deliberate rather
than missed.

`tests/conftest.py::redact_personal_data` says plainly what it covers - a home
path and the account name - and a credential is not personal data, so this is
not a bug in that function. It is a class of secret nothing owned. Every test
log, every CI artifact and every pasted failure is an echo path; CLAUDE.md
non-negotiable 12 states exactly this rule for save-header bytes and nothing
stated it for credentials.

WHY EVERY ARM HERE RUNS A REAL PYTEST SUBPROCESS. A unit call of the redactor
grades the function; it does not grade the RENDER PATH, and the render path is
where the leak happened. The report hook has to be reached for the measurement
to mean anything, so the arms drive a child pytest with `tests.conftest` loaded
as a plugin - which is what makes its hooks fire on a target outside this
rootdir - and read the child's combined output.

THE CHILD'S ENVIRONMENT IS STRIPPED OF REAL CREDENTIALS BEFORE IT STARTS, and
that is a correctness property rather than hygiene. An adversary measured the
first build's placeholder arm passing under a MUTANT, because a real key in the
inherited environment supplied the placeholder the arm was looking for. With the
environment stripped, the only credential in the child's report is the one the
arm planted, so every assertion is about that plant and the arms behave the same
here as on a CI runner that holds no key at all.

THE CONTROL THAT MAKES A GREEN MEAN SOMETHING. A child that never rendered the
frame would show no secret for a reason that has nothing to do with redaction,
and would pass. So every arm first asserts that the frame it grades actually
reached the report.

THE CONTROL IS NOT THE HOME PLACEHOLDER, AND THE REASON IS MEASURED. The first
build asserted `REDACTED_HOME` was present, on the reasoning that it proves the
report hook ran. It does not, and it is not even stable: when the child's
rootdir sits deep under the home directory - which is exactly where a
`tmp_path_factory` directory sits, and NOT where a `tempfile.mkdtemp` one sits -
pytest renders stdlib frames as RELATIVE paths, so no absolute home path is
emitted and there is nothing for the home rule to rewrite. The same child
command was measured green from a plain parent and red from a pytest parent for
that reason alone. A control that reports on how deep a temporary directory
happens to be is a control about nothing.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import (
    _CREDENTIAL_MIN_LITERAL,
    _CREDENTIAL_VARIABLES,
    REDACTED_CREDENTIAL,
    UNCOVERED_SECRETS,
    redact_credentials,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Synthetic and never real. The prefix is the vendor-assigned one the shape
#: rule anchors on; everything after it is a literal this file authored, so a
#: grep of the repository for a real key cannot match it.
PLANTED_KEY = "sk-ant-admin01-" + "Z" * 40

#: A second shape, so a green is not a statement about one prefix.
PLANTED_GH_TOKEN = "ghp_" + "Q" * 36

#: A credential with NO vendor prefix at all. Only a LITERAL rule can reach
#: this, which is what makes it the arm that grades the literal half - see
#: :func:`test_a_prefixless_secret_in_a_listed_variable_does_not_survive`.
PLANTED_BARE_TOKEN = "7f3a" * 10

#: The variable the shape arms plant under. Deliberately NOT one of the names
#: `tests/conftest.py` lists: an arm that planted a listed name would be graded
#: by the literal rule as well and would say nothing about the shape rule.
UNLISTED_VARIABLE = "CS1156_UNLISTED_PROBE"

#: The variable the literal arm plants under. Deliberately one that IS listed,
#: because a literal rule is only built for a listed name.
LISTED_VARIABLE = "CODSPEED_TOKEN"

#: The child's own program name, which pytest renders in the traceback body on
#: every run. Its presence proves the body was rendered at all.
RENDERED_BODY_MARKER = "zz-cs1156-no-such-program-zz"

#: A variable every Windows environment carries and no rule here touches. Its
#: presence proves the ENVIRONMENT DICT reached the report - which is the frame
#: this item is about, and the thing a shorter traceback would have dropped.
RENDERED_ENV_MARKER = "ALLUSERSPROFILE"

SUBPROCESS_TIMEOUT = 180

#: The leak as it was filed: a failure DURING A TEST.
#:
#: WHY THE SECRET IS BOUND TO A LOCAL AND NOT LEFT IN THE ENV DICT ALONE. The
#: first build planted it in the environment and relied on the rendered
#: ``env={...}`` argument to carry it. pytest TRUNCATES a long dict repr, and a
#: variable added last falls outside the shown portion - so the arm measured
#: nothing and passed. The local is rendered in full under ``--showlocals``, and
#: the env dict is still passed so the ALLUSERSPROFILE control still holds.
CHILD_AT_RUNTIME = """
import os
import subprocess


def test_the_env_frame_renders():
    leaked = os.environ["{variable}"]
    subprocess.run(["zz-cs1156-no-such-program-zz"], env=dict(os.environ), check=False)
"""

#: The same secret raised at MODULE level, so it fails during COLLECTION. An
#: adversary reproduced the original leak here after the first build shipped,
#: because a collection failure is rendered from a CollectReport that no hook
#: touched. There are no frame locals at module level, so the value travels in
#: the exception message - which is the ``longrepr`` and ``reprcrash`` channel
#: :func:`tests.conftest._redact_report` reads.
CHILD_AT_COLLECTION = """
import os

raise RuntimeError(
    "zz-cs1156-no-such-program-zz ALLUSERSPROFILE " + os.environ["{variable}"]
)


def test_never_reached():
    pass
"""

#: The secret through CAPTURED OUTPUT rather than through a frame or a message.
#: This is the ``report.sections`` channel, a render site no arm covered before.
CHILD_AT_STDOUT = """
import os


def test_the_captured_output_renders():
    print("zz-cs1156-no-such-program-zz", os.environ["{variable}"], "ALLUSERSPROFILE")
    raise AssertionError("forced, so the captured section is rendered")
"""


def _child_environment(plant: dict[str, str]) -> dict[str, str]:
    """This process's environment, stripped of real secrets, plus the plant.

    Two removals, for two different reasons.

    ``PYTEST_ADDOPTS`` reaches the child and can carry a ``--tb`` setting that
    suppresses the very frame an arm exists to render; ``PYTEST_CURRENT_TEST``
    travels the same way and names the parent's test in the child's output.

    Every name in :data:`_CREDENTIAL_VARIABLES` goes because a real value left
    in place would build a real literal rule in the child AND could supply the
    placeholder an arm asserts on - which is how the first build's placeholder
    arm passed under a mutant that had broken the thing it was grading.

    Args:
        plant: Variables to set in the child, after the removals.

    Returns:
        The child's environment.
    """
    listed = {name.upper() for name in _CREDENTIAL_VARIABLES}
    environment = {
        name: value
        for name, value in os.environ.items()
        if not name.upper().startswith("PYTEST_") and name.upper() not in listed
    }
    environment["PYTHONPATH"] = str(REPO_ROOT)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment.update(plant)
    return environment


def _render(root: Path, source: str, plant: dict[str, str]) -> str:
    """Run a child pytest that fails, and return its combined output.

    Args:
        root: A directory of this arm's own, so two arms cannot overwrite each
            other's module.
        source: The child module's text.
        plant: Environment variables to set in the child.

    Returns:
        The child's combined output, exactly as a log or a CI artifact would
        hold it. NOTHING is scrubbed here - scrubbing on this side would grade
        this file instead of the render path.
    """
    root.mkdir(parents=True, exist_ok=True)
    target = root / "test_cs1156_child.py"
    target.write_text(source, encoding="ascii")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(target),
            "-p",
            "tests.conftest",
            "-p",
            "no:randomly",
            "-p",
            "no:cacheprovider",
            "--rootdir",
            str(root),
            # EXPLICIT, never inherited: the frame carrying the environment dict
            # is the subject, so the arm states the traceback style it grades
            # rather than taking whatever the parent run happened to set.
            "--tb=long",
            # The secret is bound to a FRAME LOCAL in the runtime child, for the
            # reason stated beside CHILD_AT_RUNTIME: a long env dict repr is
            # truncated and a variable added last falls outside it.
            "--showlocals",
        ],
        capture_output=True,
        check=False,
        cwd=str(root),
        env=_child_environment(plant),
        timeout=SUBPROCESS_TIMEOUT,
    )
    return (completed.stdout + completed.stderr).decode("utf-8", errors="replace")


def _tail(rendered: str) -> str:
    """The last of a child report, for a failure message a reader can act on."""
    return rendered[-1200:]


def _assert_the_frame_was_rendered(rendered: str) -> None:
    """THE CONTROL. Without it every assertion below passes on a child that rendered nothing."""
    assert RENDERED_BODY_MARKER in rendered, _tail(rendered)
    assert RENDERED_ENV_MARKER in rendered, _tail(rendered)


@pytest.fixture(scope="module")
def rendered_key(tmp_path_factory: pytest.TempPathFactory) -> str:
    """One child run, shared by the arms that read it."""
    return _render(
        tmp_path_factory.mktemp("cs1156_key"),
        CHILD_AT_RUNTIME.format(variable=UNLISTED_VARIABLE),
        {UNLISTED_VARIABLE: PLANTED_KEY},
    )


def test_the_env_frame_reached_the_report(rendered_key: str) -> None:
    """THE CONTROL, as an arm of its own so it fails by name when the harness drifts."""
    _assert_the_frame_was_rendered(rendered_key)


def test_a_planted_key_does_not_survive_a_rendered_env_frame(rendered_key: str) -> None:
    """CS-1156: the exact shape that leaked on 2026-09-19, through the real render path."""
    _assert_the_frame_was_rendered(rendered_key)
    assert PLANTED_KEY not in rendered_key, _tail(rendered_key)


def test_the_placeholder_is_what_replaced_it(rendered_key: str) -> None:
    """Absence alone passes for a collapsed report. The placeholder pins the substitution.

    This arm is only worth anything because the child's environment was
    stripped: with a real key left in place it passed under a mutant that had
    narrowed the rule so far it no longer matched the planted key at all.
    """
    _assert_the_frame_was_rendered(rendered_key)
    assert REDACTED_CREDENTIAL in rendered_key, _tail(rendered_key)


def test_a_second_vendor_shape_does_not_survive_either(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """One prefix covered is a statement about one prefix."""
    rendered = _render(
        tmp_path_factory.mktemp("cs1156_gh"),
        CHILD_AT_RUNTIME.format(variable=UNLISTED_VARIABLE),
        {UNLISTED_VARIABLE: PLANTED_GH_TOKEN},
    )
    _assert_the_frame_was_rendered(rendered)
    assert PLANTED_GH_TOKEN not in rendered, _tail(rendered)
    assert REDACTED_CREDENTIAL in rendered, _tail(rendered)


def test_a_prefixless_secret_in_a_listed_variable_does_not_survive(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """THE LITERAL HALF, and nothing else in this file grades it.

    An adversary emptied :data:`_CREDENTIAL_VARIABLES` to ``()`` - deleting the
    entire literal rule kind - and every arm stayed green, because every arm
    planted under an UNLISTED name and every planted value carried a vendor
    prefix a shape rule could reach. The value here carries no prefix any shape
    matches, so only a literal built from the listed variable can catch it.
    """
    assert len(PLANTED_BARE_TOKEN) >= _CREDENTIAL_MIN_LITERAL, PLANTED_BARE_TOKEN
    assert LISTED_VARIABLE in _CREDENTIAL_VARIABLES, LISTED_VARIABLE

    rendered = _render(
        tmp_path_factory.mktemp("cs1156_bare"),
        CHILD_AT_RUNTIME.format(variable=LISTED_VARIABLE),
        {LISTED_VARIABLE: PLANTED_BARE_TOKEN},
    )
    _assert_the_frame_was_rendered(rendered)
    assert PLANTED_BARE_TOKEN not in rendered, _tail(rendered)
    assert REDACTED_CREDENTIAL in rendered, _tail(rendered)


def test_a_credential_does_not_survive_a_collection_failure(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """The gap an adversary found AFTER the first build shipped.

    The same leaking frame at module level fails during collection, which pytest
    renders from a CollectReport. Measured on the first build: the planted key
    printed three times and the placeholder zero.
    """
    rendered = _render(
        tmp_path_factory.mktemp("cs1156_collect"),
        CHILD_AT_COLLECTION.format(variable=UNLISTED_VARIABLE),
        {UNLISTED_VARIABLE: PLANTED_KEY},
    )
    _assert_the_frame_was_rendered(rendered)
    assert PLANTED_KEY not in rendered, _tail(rendered)
    assert REDACTED_CREDENTIAL in rendered, _tail(rendered)


def test_a_credential_does_not_survive_captured_output(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """The ``report.sections`` render site, which no arm covered before.

    A secret printed by a failing test reaches the terminal through the captured
    stdout section rather than through a frame argument, so it exercises a
    different one of the seven sites the render path redacts at.
    """
    rendered = _render(
        tmp_path_factory.mktemp("cs1156_stdout"),
        CHILD_AT_STDOUT.format(variable=UNLISTED_VARIABLE),
        {UNLISTED_VARIABLE: PLANTED_KEY},
    )
    _assert_the_frame_was_rendered(rendered)
    assert PLANTED_KEY not in rendered, _tail(rendered)
    assert REDACTED_CREDENTIAL in rendered, _tail(rendered)


def test_the_live_environment_holds_no_credential_the_redactor_leaves_standing() -> None:
    """The LIVE arm. The other arms plant; this one reads what this machine carries.

    A fixture that is correct does not make a live arm - the value that leaked
    was a real one, so the measurement has to be taken against real ones.

    IT ASSERTS WHOLE-VALUE REPLACEMENT, NOT MERELY THAT SOMETHING CHANGED. The
    first build asked only whether redaction moved the string, and an adversary
    measured that passing on a PARTIAL redaction: a key whose prefix matched and
    whose tail did not came back as the placeholder followed by real bytes, and
    the arm scored it clean. Residue beside a placeholder is worse than no
    redaction, because it reads as handled.
    """
    standing = sorted(
        name
        for name, value in os.environ.items()
        if _looks_like_a_credential(value)
        and redact_credentials(value.strip()) != REDACTED_CREDENTIAL
    )
    assert standing == [], standing


def test_every_uncovered_secret_is_declared_and_still_uncovered() -> None:
    """A stated exemption that quietly starts working is drift too.

    The mirror of ``tests/test_report_redaction_classes.py``'s arm over
    ``UNCOVERED_CLASSES``: each declaration carries a reason, and the one that
    can be probed is probed rather than believed.
    """
    assert set(UNCOVERED_SECRETS) == {
        "unlisted-and-unprefixed",
        "not-in-the-environment",
        "internal-errors",
    }, sorted(UNCOVERED_SECRETS)
    assert all(reason.strip() for reason in UNCOVERED_SECRETS.values()), sorted(UNCOVERED_SECRETS)

    # The probe for "unlisted-and-unprefixed": a secret-shaped value carrying no
    # vendor prefix, held in no listed variable, passes through UNCHANGED. If
    # this ever starts being redacted, the declaration is stale and must move.
    unreachable = "9c2e" * 12
    assert redact_credentials(unreachable) == unreachable, unreachable


def _looks_like_a_credential(value: str) -> bool:
    """An INDEPENDENT oracle, derived from the vendor prefixes and not from the rules.

    Deliberately NOT ``tests/conftest.py``'s own patterns: an oracle built from
    the thing it grades agrees with it by construction and can observe nothing.
    """
    lowered = value.strip().lower()
    return any(
        lowered.startswith(prefix)
        for prefix in ("sk-ant-", "ghp_", "gho_", "ghs_", "ghu_", "github_pat_")
    )
