"""CS-939 - the arms over the tracked tree and over every reachable blob.

THE DEFECT THIS ANSWERS. ``tools/precommit_gate.py`` runs over STAGED bytes or
over explicitly named files, so it can only ever see what is changing now. A
credential that landed before the gate existed - or in a commit the gate was
not wired for - is invisible to it forever, because nothing ever re-reads what
already landed. A sibling project on the channel measured exactly that class: a
live token tracked from its initial commit for 133 days, green on every
working-tree check.

THE DERIVATION IS ``tests/secret_sweep_guard.py``; this file holds the arms and
the controls. The split is the one every guard family in this tree uses and it
keeps both halves under the size ceiling ``tests/data/test_phase2_gate.py``
holds every file under ``tests/`` to.

THE DETECTOR IS IMPORTED, NEVER RESTATED, and one arm proves it rather than
asserting it in prose: :func:`test_the_sweep_reads_the_gates_own_pattern_list`
replaces ``SECRET_PATTERNS`` on the gate module and requires the verdict to
move. A copy of the list in this family would survive that replacement and
report the same answer, which is the whole failure mode the clause names.

THE SYNTHETIC FIXTURE THAT MUST NOT REDDEN IS NOT A FORGIVENESS TABLE. This
tree's oldest answer to "how do you write a credential-shaped fixture into a
tracked file" is to ASSEMBLE it from fragments and never spell it - see
``tools/outbound_gate.py::CREDENTIAL_CANARIES``. The joined value matches the
gate's AWS rule; the source that builds it matches nothing. So the fixture's
own source line is the control, and it is a mechanism rather than a recorded
exception: no entry anywhere forgives this file, and a real credential added to
it would redden the live arm exactly as it would redden any other file.

THE CHARSET LEG IS THE SIBLING SWEEP, NOT SCOPE CREEP. It shares the root cause
exactly - a check that reads only what is changing now cannot see a byte that
already landed - so it is swept here with an arm of its own rather than filed
as a fresh discovery. CLAUDE.md non-negotiable 4 is the rule it answers.

NO FIGURE IS RESTATED IN AN ASSERTION. The live arms pin ZERO findings, so they
cannot go stale; the anti-vacuity arms pin the POPULATION instead, because a
sweep of nothing and a sweep that found nothing render the same way and only
the second is worth anything.
"""

from __future__ import annotations

import re

import pytest

from tests import secret_sweep_guard as sweep

# Assembled, never spelled. The joined value matches the gate's AWS access key
# rule and no branch of PLACEHOLDER_RE; this line, which builds it, matches
# neither - which is precisely the property the fixture control asserts.
SYNTHETIC_CREDENTIAL = "AKIA" + ("Q7" * 8)

#: The source spelling of the line above, as a fixture reads on disk.
ASSEMBLED_SPELLING = 'SYNTHETIC_CREDENTIAL = "AKIA" + ("Q7" * 8)'

#: One byte outside 7-bit ASCII, for the charset control. Spelled as an escape,
#: so this file stays inside the rule it is testing.
NON_ASCII_LINE = b"a non-ascii byte follows: \xc3\xa9\n"


def planted_line(field: str, value: str) -> bytes:
    """Build ``<field> = <value>`` as one line of bytes.

    THE FIELD NAME IS A PARAMETER RATHER THAN PART OF A LITERAL, and that is
    not tidiness. Spelling the field name, an equals sign and a quote next to
    each other at a call site is the gate's quoted-literal rule exactly - and
    the live arm below reported all three call sites in THIS file on its first
    run, before this helper existed. The arm has teeth on the module that owns
    it, which is the strongest evidence it has teeth at all.

    Args:
        field: The credential-shaped field name to write.
        value: The value to assign it.

    Returns:
        The line, ASCII-encoded and newline-terminated.
    """
    return (field + " = " + value + chr(10)).encode("ascii")


# --- controls: the sweep discriminates, on a corpus with no repository in it -


def test_a_planted_credential_in_a_tracked_file_is_reported(tmp_path) -> None:
    """The control that gives the live arm its teeth.

    A sweep that reported nothing because it read nothing renders exactly like
    a clean tree, so the live arm below is worth nothing without this.
    """
    planted = tmp_path / "config.py"
    planted.write_bytes(planted_line("access_key", SYNTHETIC_CREDENTIAL))

    findings = sweep.sweep_paths(["config.py"], tmp_path)

    assert len(findings) == 1, findings
    assert "config.py" in findings[0], findings


def test_the_assembled_spelling_of_the_same_credential_is_not_reported(tmp_path) -> None:
    """The fixture leg, and it DISCRIMINATES rather than merely staying green.

    Both legs run on the same sweep in the same call. A predicate that reported
    nothing at all would pass the fixture leg and fail the planted one, so the
    pair says the sweep tells the two apart.
    """
    fixture = tmp_path / "fixture.py"
    fixture.write_bytes((ASSEMBLED_SPELLING + chr(10)).encode("ascii"))
    planted = tmp_path / "leaked.py"
    planted.write_bytes(planted_line("token", SYNTHETIC_CREDENTIAL))

    findings = sweep.sweep_paths(["fixture.py", "leaked.py"], tmp_path)

    assert [line for line in findings if "fixture.py" in line] == [], findings
    assert [line for line in findings if "leaked.py" in line] != [], findings


def test_the_sweep_reads_the_gates_own_pattern_list(tmp_path, monkeypatch) -> None:
    """The anti-restatement arm, proven by substitution rather than by reading.

    The clause asks for the gate's detector to be IMPORTED rather than
    restated. A restatement is invisible to a source read - two identical lists
    look alike - so the property is measured by replacing the gate's list with
    one that judges something else entirely and requiring the verdict to follow
    it.
    """
    carrier = tmp_path / "prose.md"
    carrier.write_bytes(b"the word marmalade appears here\n")

    assert sweep.sweep_paths(["prose.md"], tmp_path) == []

    monkeypatch.setattr(
        sweep.gate(),
        "SECRET_PATTERNS",
        [(re.compile("marmalade"), "the substituted rule")],
    )
    findings = sweep.sweep_paths(["prose.md"], tmp_path)

    assert len(findings) == 1, findings
    assert "the substituted rule" in findings[0], findings


def test_an_item_the_gate_itself_would_decline_is_not_scanned(tmp_path) -> None:
    """Admission is the gate's own, so the sweep reports only blockable things.

    A sweep that scanned what the gate skips would report findings no commit
    could ever have been blocked for, which is a guard nobody can act on.
    """
    binary = tmp_path / "world.sav"
    binary.write_bytes(planted_line("access_key", SYNTHETIC_CREDENTIAL))
    text = tmp_path / "world.py"
    text.write_bytes(planted_line("access_key", SYNTHETIC_CREDENTIAL))

    findings = sweep.sweep_paths(["world.sav", "world.py"], tmp_path)

    assert [line for line in findings if "world.sav" in line] == [], findings
    assert [line for line in findings if "world.py" in line] != [], findings


def test_a_planted_non_ascii_byte_is_reported(tmp_path) -> None:
    """The charset leg's control, and its discriminating half."""
    offender = tmp_path / "note.md"
    offender.write_bytes(NON_ASCII_LINE)
    clean = tmp_path / "clean.md"
    clean.write_bytes(b"plain ascii prose\n")

    findings = sweep.sweep_paths(["note.md", "clean.md"], tmp_path, check=sweep.charset_findings)

    assert [line for line in findings if "clean.md" in line] == [], findings
    assert [line for line in findings if "note.md" in line] != [], findings


def test_a_planted_blob_is_reported() -> None:
    """The blob leg's control, on an injected corpus with no git involved.

    The reader is injected for the same reason the citation family injects its
    sources: a control that had to write a real object into a real object store
    would be a control that mutates the repository it is grading.
    """
    corpus = {
        "0" * 40: b"nothing here\n",
        "1" * 40: planted_line("api_key", SYNTHETIC_CREDENTIAL),
    }
    blobs = [(sha, "settings.py") for sha in sorted(corpus)]

    findings = sweep.blob_findings(blobs, read=lambda shas: [(sha, corpus[sha]) for sha in shas])

    assert len(findings) == 1, findings
    assert "1" * 40 in findings[0], findings


def test_a_blob_the_reader_never_yields_is_a_failure_rather_than_a_pass() -> None:
    """A reader that silently drops a blob must not render as a clean blob.

    This is the shape that makes a sweep lie: the population is counted, the
    scan is skipped, and the report is identical to the one a clean object
    would produce.
    """
    blobs = [("0" * 40, "a.py"), ("1" * 40, "b.py")]

    with pytest.raises(RuntimeError, match="did not yield"):
        sweep.blob_findings(blobs, read=lambda _shas: [("0" * 40, b"fine\n")])


# --- the live arms, over the repository this suite is running in -------------


def test_no_tracked_file_carries_a_credential_the_gate_would_block() -> None:
    """Every tracked file, read from the working tree, against the gate's rules."""
    findings = sweep.sweep_paths(sweep.tracked_paths(), sweep.REPO_ROOT)

    assert findings == [], findings


def test_no_tracked_file_carries_a_byte_outside_the_charset_rule() -> None:
    """The sibling sweep, over the same population and the same blindness."""
    findings = sweep.sweep_paths(
        sweep.tracked_paths(), sweep.REPO_ROOT, check=sweep.charset_findings
    )

    assert findings == [], findings


def test_every_tracked_python_and_markdown_file_is_actually_scanned() -> None:
    """Anti-vacuity. A clean sweep and a sweep of nothing render the same.

    THE FLOOR IS EXACT RATHER THAN A ROUND NUMBER, and it is chosen so a
    legitimately binary file added tomorrow cannot redden it: ``.py`` and
    ``.md`` are both in the gate's own TEXT_EXTS, so every one of them is
    admitted unless it is past the content cap.
    """
    scanned = set(sweep.scanned_paths(sweep.tracked_paths(), sweep.REPO_ROOT))
    expected = {
        path
        for path in sweep.tracked_paths()
        if path.endswith((".py", ".md")) and (sweep.REPO_ROOT / path).is_file()
    }

    assert expected, "the tracked tree carries no python or markdown at all"
    assert expected - scanned == set(), sorted(expected - scanned)


@pytest.mark.slow
def test_no_reachable_blob_carries_a_credential_the_gate_would_block() -> None:
    """Every blob reachable from every ref, which is the history half.

    ON A SHALLOW CHECKOUT THIS IS THE TIP TREE AND NOTHING MORE, and that is
    honest rather than a hole: the population is whatever the checkout reaches,
    the anti-vacuity arm below pins that it is at least the tracked tree, and a
    full-history checkout - the pre-push hook on a developer's box, and tier
    2's clean-checkout probe - sweeps the whole of it.
    """
    findings = sweep.blob_findings(sweep.reachable_blobs())

    assert findings == [], findings


@pytest.mark.slow
def test_no_reachable_blob_carries_a_byte_outside_the_charset_rule() -> None:
    """The sibling sweep, over the history population."""
    findings = sweep.blob_findings(sweep.reachable_blobs(), check=sweep.charset_findings)

    assert findings == [], findings


def test_the_blob_population_covers_at_least_the_tracked_tree() -> None:
    """Anti-vacuity for the blob leg, floored on a population git must reach.

    Every tracked file's current content is a blob reachable from HEAD, so the
    blob count can never honestly fall below the tracked-file count - and a
    walk that returned nothing fails here rather than rendering clean.
    """
    blobs = sweep.reachable_blobs()
    tracked = sweep.tracked_paths()

    assert len(blobs) >= len(tracked), (len(blobs), len(tracked))
