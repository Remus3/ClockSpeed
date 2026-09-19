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

THE CONTROL THAT MAKES A GREEN MEAN SOMETHING. A child that never rendered the
frame at all would show no secret for a reason that has nothing to do with
redaction, and would pass. So every arm first asserts that the traceback body
AND the environment dict were rendered, and only then is the absence of the
secret evidence about redaction.

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

from tests.conftest import REDACTED_CREDENTIAL, redact_credentials

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Synthetic and never real. The prefix is the vendor-assigned one the shape
#: rule anchors on; everything after it is a literal this file authored, so a
#: grep of the repository for a real key cannot match it.
PLANTED_KEY = "sk-ant-admin01-" + "Z" * 40

#: A second shape, so a green is not a statement about one prefix.
PLANTED_GH_TOKEN = "ghp_" + "Q" * 36

#: The variable the child plants the key under. Deliberately NOT one of the
#: names `tests/conftest.py` lists: an arm that planted a listed name would be
#: graded by the literal rule and would say nothing about the shape rule, which
#: is the half that covers a credential arriving under a name nobody listed.
UNLISTED_VARIABLE = "CS1156_UNLISTED_PROBE"

#: The child's own program name, which pytest renders in the traceback body on
#: every run. Its presence proves the body was rendered at all.
RENDERED_BODY_MARKER = "zz-cs1156-no-such-program-zz"

#: A variable every Windows environment carries and no rule here touches. Its
#: presence proves the ENVIRONMENT DICT reached the report - which is the frame
#: this item is about, and the thing a shorter traceback would have dropped.
RENDERED_ENV_MARKER = "ALLUSERSPROFILE"

SUBPROCESS_TIMEOUT = 180

_CHILD = """
import os
import subprocess


def test_the_env_frame_renders():
    env = dict(os.environ)
    env["{variable}"] = "{secret}"
    subprocess.run(["zz-cs1156-no-such-program-zz"], env=env, check=False)
"""


def _render_a_failing_env_frame(root: Path, secret: str, variable: str) -> str:
    """Run a child pytest whose failure renders a whole environment dict.

    Args:
        root: A directory of this arm's own. Named per arm so two arms cannot
            overwrite each other's module.
        secret: The credential-shaped string to plant in the child's env.
        variable: The environment variable to plant it under.

    Returns:
        The child's combined output, exactly as a log or a CI artifact would
        hold it. NOTHING is scrubbed here - scrubbing on this side would grade
        this file instead of the render path.
    """
    root.mkdir(parents=True, exist_ok=True)
    target = root / "test_cs1156_child.py"
    target.write_text(_CHILD.format(variable=variable, secret=secret), encoding="ascii")

    environment = {
        name: value
        for name, value in os.environ.items()
        # PYTEST_ADDOPTS reaches the child and can carry a --tb setting that
        # suppresses the very frame this arm exists to render. PYTEST_CURRENT_TEST
        # travels the same way and names the parent's test in the child's output.
        if not name.upper().startswith("PYTEST_")
    }
    environment["PYTHONPATH"] = str(REPO_ROOT)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
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
        ],
        capture_output=True,
        check=False,
        cwd=str(root),
        env=environment,
        timeout=SUBPROCESS_TIMEOUT,
    )
    return (completed.stdout + completed.stderr).decode("utf-8", errors="replace")


def _tail(rendered: str) -> str:
    """The last of a child report, for a failure message a reader can act on."""
    return rendered[-1200:]


@pytest.fixture(scope="module")
def rendered_key(tmp_path_factory: pytest.TempPathFactory) -> str:
    """One child run, shared by the arms that read it."""
    return _render_a_failing_env_frame(
        tmp_path_factory.mktemp("cs1156_key"), PLANTED_KEY, UNLISTED_VARIABLE
    )


def _assert_the_frame_was_rendered(rendered: str) -> None:
    """THE CONTROL. Without it every assertion below passes on a child that rendered nothing."""
    assert RENDERED_BODY_MARKER in rendered, _tail(rendered)
    assert RENDERED_ENV_MARKER in rendered, _tail(rendered)


def test_the_env_frame_reached_the_report(rendered_key: str) -> None:
    """THE CONTROL, as an arm of its own so it fails by name when the harness drifts."""
    _assert_the_frame_was_rendered(rendered_key)


def test_a_planted_key_does_not_survive_a_rendered_env_frame(rendered_key: str) -> None:
    """CS-1156: the exact shape that leaked on 2026-09-19, through the real render path."""
    _assert_the_frame_was_rendered(rendered_key)
    assert PLANTED_KEY not in rendered_key, _tail(rendered_key)


def test_the_placeholder_is_what_replaced_it(rendered_key: str) -> None:
    """Absence alone passes for a collapsed report. The placeholder pins the substitution."""
    _assert_the_frame_was_rendered(rendered_key)
    assert REDACTED_CREDENTIAL in rendered_key, _tail(rendered_key)


def test_a_second_vendor_shape_does_not_survive_either(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """One prefix covered is a statement about one prefix."""
    rendered = _render_a_failing_env_frame(
        tmp_path_factory.mktemp("cs1156_gh"), PLANTED_GH_TOKEN, UNLISTED_VARIABLE
    )
    _assert_the_frame_was_rendered(rendered)
    assert PLANTED_GH_TOKEN not in rendered, _tail(rendered)


def test_the_live_environment_holds_no_credential_the_redactor_misses() -> None:
    """The LIVE arm. The other arms plant; this one reads what this machine actually carries.

    A fixture that is correct does not make a live arm - the value that leaked
    was a real one, so the measurement has to be taken against real ones. Every
    value in this process's environment that the redactor itself recognises as
    a credential must be rewritten by it; a value it recognises and leaves
    standing is the defect, live.
    """
    leaked = sorted(
        name
        for name, value in os.environ.items()
        if value and redact_credentials(value) == value and _looks_like_a_credential(value)
    )
    assert leaked == [], leaked


def _looks_like_a_credential(value: str) -> bool:
    """An INDEPENDENT oracle, derived from the vendor prefixes and not from the rules.

    Deliberately NOT ``tests/conftest.py``'s own patterns: an oracle built from
    the thing it grades agrees with it by construction and can observe nothing.
    """
    lowered = value.lower()
    return any(lowered.startswith(prefix) for prefix in ("sk-ant-", "ghp_", "gho_", "github_pat_"))
