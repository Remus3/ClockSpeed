"""CS-1292 - the README public-readiness audit, held as tests.

The acceptance (``docs/item_notes/phase7.md``, CS-1292) quotes MAIN's README
audit: a README under about 220 lines with an image, a short Quickstart with the
remaining install detail in one linked doc (the environment-variable table
included), a banner plus one dashboard screenshot under ``docs/assets/``, "no
language model" said only in At a glance, the Python version stated once and only
in Requirements, one copyright-holder string shared by ``LICENSE`` and
``CITATION.cff``, and no absolute checkout path in ``docs/LEDGER.md`` or
``docs/history_notes.md``.

Each clause is its own test so one regression is one red line. No assertion
message renders a matched path - a line number names the hit - because a clone
under a home directory would otherwise echo that home path.
"""

from __future__ import annotations

import re
import struct
import sys
import tomllib
from pathlib import Path
from typing import Final

import pytest

from clockspeed.data import locate
from clockspeed.surface import config

_TOOLS_DIR: Final = Path(__file__).resolve().parents[1] / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import doc_sweep  # noqa: E402

#: MAIN's stated budget: "README under ~220 lines".
README_LINE_BUDGET: Final = 220

#: A banner plus one dashboard screenshot.
ASSET_IMAGES: Final = 2

#: "a Quickstart of about 10 lines" - prose and command lines; fences and a
#: thematic break are layout, not lines of the Quickstart.
QUICKSTART_LINE_BUDGET: Final = 10

#: The banner: the README's FIRST image, above its first section.
BANNER: Final = "docs/assets/social-preview.png"

#: Every fenced command line the README's install section carried before CS-1292
#: moved it, each of which docs/OPERATIONS.md section 1.2 must still hold.
MOVED_COMMANDS: Final = (
    "python --version",
    "git --version",
    "python -m venv .venv",
    ".venv\\Scripts\\activate",
    'python -m pip install -e ".[dev]"',
    "Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force",
    "python scripts/install_hooks.py",
    "python scripts/verify_env.py",
    'set "PATH=%PATH%;<Git install>\\usr\\bin"',
    "python scripts/make_cert.py",
    "python -m clockspeed.surface",
    'curl.exe -s -k -X POST "https://localhost:<port>/api/solve?targets=Desc_IronIngot_C=30'
    '&recipes=Recipe_IngotIron_C&raw_items=Desc_OreIron_C&byproduct_policy=balanced"',
)

#: The inline commands that install section spelled in prose.
MOVED_INLINE: Final = (
    "`source .venv/Scripts/activate`",
    '`$env:Path += ";<Git install>\\usr\\bin"`',
    "`git --exec-path`",
    "`openssl version`",
    "`python -m clockspeed.surface --help`",
)

#: The dashboard flags its option table named; section 7.2's flag table owns them now.
MOVED_FLAGS: Final = ("`--port", "`--cert-dir", "`--no-world`")

#: The PNG chunk types an image may carry. Everything else - tEXt, zTXt, iTXt,
#: eXIf, tIME and any private chunk - can hold text a renderer stamped in, so it
#: is refused rather than enumerated.
PNG_ALLOWED_CHUNKS: Final = frozenset(
    {b"IHDR", b"PLTE", b"tRNS", b"IDAT", b"IEND", b"sRGB", b"gAMA", b"cHRM", b"pHYs"}
)

PNG_SIGNATURE: Final = b"\x89PNG\r\n\x1a\n"

#: A drive-rooted spelling of the project folder, any case: ``X:\Clockspeed`` or
#: ``X:/Clockspeed``, and Git Bash's ``/x/Clockspeed`` for any drive letter.
ABSOLUTE_CHECKOUT_RE: Final = re.compile(
    r"(?:[A-Za-z]:[\\/]+|(?<![\w.~/-])/[A-Za-z]/)Clockspeed", re.IGNORECASE
)

#: The two docs the acceptance names, plus the two this item rewrote.
AUDITED_DOCS: Final = ("docs/LEDGER.md", "docs/history_notes.md", "README.md", "docs/OPERATIONS.md")

#: A Python-version-shaped token, whole: 3.N or 3.NN plus any further ``.N`` parts,
#: so ``3.13.0`` is one token and never equals the floor ``3.13``.
PY_VERSION_RE: Final = re.compile(r"(?<![\d.])3\.\d{1,2}(?:\.\d+)*(?![\d.])")

IMAGE_RE: Final = re.compile(r"!\[[^\]]*\]\((?P<target>[^)\s]+)\)")

#: Every environment override the moved install table documents.
ENV_OVERRIDES: Final = (
    locate.ENV_GAME_DIR,
    locate.ENV_SAVE_ROOT,
    locate.ENV_ACCOUNT_DIR,
    locate.ENV_LOCAL_CONFIG,
    config.CERT_DIR_ENV,
    config.PORT_ENV,
)


def _readme(repo_root: Path) -> str:
    return (repo_root / "README.md").read_text(encoding="ascii")


def _operations(repo_root: Path) -> str:
    return (repo_root / "docs" / "OPERATIONS.md").read_text(encoding="ascii")


def _subsection(markdown: str, prefix: str) -> str:
    """The lines from the heading starting ``prefix`` to the next ``##`` or ``###`` heading."""
    lines = markdown.splitlines()
    starts = [n for n, line in enumerate(lines) if line.startswith(prefix)]
    assert len(starts) == 1, f"{len(starts)} heading(s) start {prefix!r}"
    end = next(
        (n for n in range(starts[0] + 1, len(lines)) if re.match(r"#{2,3} ", lines[n])),
        len(lines),
    )
    return "\n".join(lines[starts[0] : end])


def _sections(markdown: str) -> dict[str, str]:
    """Body text keyed by ``## `` heading; the text above the first one is ``""``."""
    sections: dict[str, list[str]] = {"": []}
    current = ""
    for line in markdown.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        else:
            sections[current].append(line)
    return {name: "\n".join(lines) for name, lines in sections.items()}


def _png_chunks(data: bytes) -> list[bytes]:
    assert data.startswith(PNG_SIGNATURE), "not a PNG signature"
    chunks: list[bytes] = []
    offset = len(PNG_SIGNATURE)
    while offset < len(data):
        (length,) = struct.unpack(">I", data[offset : offset + 4])
        chunks.append(data[offset + 4 : offset + 8])
        offset += 12 + length
    return chunks


def test_readme_is_under_the_line_budget(repo_root: Path) -> None:
    lines = _readme(repo_root).splitlines()
    assert len(lines) <= README_LINE_BUDGET, f"README.md has {len(lines)} lines"


def test_readme_shows_a_banner_and_a_dashboard_screenshot(repo_root: Path) -> None:
    text = _readme(repo_root)
    targets = [m.group("target") for m in IMAGE_RE.finditer(text)]
    assets = [t for t in targets if t.startswith("docs/assets/") and t.endswith(".png")]
    assert len(assets) >= ASSET_IMAGES, f"README.md shows {len(assets)} docs/assets PNG(s)"
    for target in assets:
        assert (repo_root / target).is_file(), f"README image {target} does not exist"
    first = IMAGE_RE.search(text)
    assert first is not None, "README.md shows no image"
    assert first.group("target") == BANNER, f"the first image is {first.group('target')}"
    assert first.start() < text.find("\n## "), "the banner is not above the first section"


def test_asset_pngs_carry_no_text_metadata(repo_root: Path) -> None:
    pngs = sorted((repo_root / "docs" / "assets").glob("*.png"))
    assert len(pngs) >= ASSET_IMAGES, f"docs/assets holds {len(pngs)} PNG(s)"
    for png in pngs:
        chunks = _png_chunks(png.read_bytes())
        extra = sorted(c.decode("latin-1") for c in set(chunks) - PNG_ALLOWED_CHUNKS)
        assert not extra, f"{png.name} carries chunk(s) {extra}"
        assert chunks[0] == b"IHDR", f"{png.name} does not open with IHDR"
        assert chunks[-1] == b"IEND", f"{png.name} does not close with IEND"


def test_language_model_is_named_only_in_at_a_glance(repo_root: Path) -> None:
    hits = {
        name: len(re.findall(r"language model", body, re.IGNORECASE))
        for name, body in _sections(_readme(repo_root)).items()
    }
    assert hits.get("At a glance", 0) == 1, "At a glance must name it exactly once"
    elsewhere = {name or "(preamble)": n for name, n in hits.items() if n and name != "At a glance"}
    assert not elsewhere, f"also named in {elsewhere}"


def test_citation_leaves_the_language_model_claim_to_the_readme(repo_root: Path) -> None:
    """MAIN's item 4 counts CITATION.cff as one more repetition of the claim."""
    cff = (repo_root / "CITATION.cff").read_text(encoding="ascii")
    assert not re.search(r"language model", cff, re.IGNORECASE), "CITATION.cff repeats it"


def test_python_version_is_stated_once_in_requirements(repo_root: Path) -> None:
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    floor = pyproject["project"]["requires-python"].removeprefix(">=")
    hits = {
        name: PY_VERSION_RE.findall(body)
        for name, body in _sections(_readme(repo_root)).items()
        if PY_VERSION_RE.search(body)
    }
    assert hits == {"Requirements": [floor]}, f"version tokens by section: {hits}"


def test_quickstart_is_short_and_links_the_install_doc(repo_root: Path) -> None:
    sections = _sections(_readme(repo_root))
    assert "Quickstart" in sections, "README.md has no Quickstart section"
    body = [
        line
        for line in sections["Quickstart"].splitlines()
        if line.strip() and not line.startswith("```") and line.strip() != "---"
    ]
    assert len(body) <= QUICKSTART_LINE_BUDGET, f"Quickstart has {len(body)} lines"


def test_the_quickstart_link_lands_on_a_real_install_heading(repo_root: Path) -> None:
    """Every README fragment into docs/OPERATIONS.md resolves there, GitHub's rule.

    The Quickstart must carry one; the Requirements table's openssl row carries
    another, and both are resolved against the target's real headings.
    """
    link = re.compile(r"\]\(docs/OPERATIONS\.md#([^)\s]+)\)")
    quickstart = _sections(_readme(repo_root)).get("Quickstart", "")
    assert link.search(quickstart), "Quickstart links no heading of docs/OPERATIONS.md"
    landed = doc_sweep.anchors(_operations(repo_root))
    fragments = link.findall(_readme(repo_root))
    missing = [fragment for fragment in fragments if fragment not in landed]
    assert not missing, f"README fragment(s) {missing} name no heading"


def test_section_1_2_holds_every_moved_command(repo_root: Path) -> None:
    """Nothing the README's install section spelled was dropped on the way to section 1.2."""
    operations = _operations(repo_root)
    section = _subsection(operations, "### 1.2 ")
    fenced = {
        line.strip()
        for block in re.findall(r"^```[^\n]*\n(.*?)^```", section, re.MULTILINE | re.DOTALL)
        for line in block.splitlines()
    }
    missing = [command for command in MOVED_COMMANDS if command not in fenced]
    assert not missing, f"section 1.2 lacks fenced command(s) {missing}"
    absent = [inline for inline in MOVED_INLINE if inline not in section]
    assert not absent, f"section 1.2 lacks inline command(s) {absent}"
    flags = _subsection(operations, "### 7.2 ")
    unowned = [flag for flag in MOVED_FLAGS if f"| {flag}" not in flags]
    assert not unowned, f"section 7.2 owns no row for {unowned}"


def test_env_var_table_lives_in_the_install_doc(repo_root: Path) -> None:
    readme = _readme(repo_root)
    section = _subsection(_operations(repo_root), "### 1.2 ")
    for name in ENV_OVERRIDES:
        row = f"| `{name}` |"
        assert row not in readme, f"README.md still carries the {name} row"
        assert row in section, f"docs/OPERATIONS.md section 1.2 has no {name} row"


def test_license_holder_matches_citation_authors(repo_root: Path) -> None:
    license_text = (repo_root / "LICENSE").read_text(encoding="ascii")
    match = re.search(r"^Copyright \(c\) [0-9]{4}(?:-[0-9]{4})? (.+)$", license_text, re.MULTILINE)
    assert match is not None, "LICENSE has no 'Copyright (c) <year> <holder>' line"
    holder = match.group(1).strip()
    cff = (repo_root / "CITATION.cff").read_text(encoding="ascii")
    block = re.search(r"^authors:\n((?:[ -].*\n)+)", cff, re.MULTILINE)
    assert block is not None, "CITATION.cff has no authors block"
    names = re.findall(r"^\s*-?\s*name:\s*(.+?)\s*$", block.group(1), re.MULTILINE)
    assert names == [holder], f"CITATION.cff authors {names} != LICENSE holder [{holder!r}]"


@pytest.mark.parametrize(
    ("text", "hit"),
    [
        ("root is C:\\Clockspeed now", True),
        ("`e:/clockspeed/tools/x.py`", True),
        ("`cd /c/Clockspeed && <cmd>`", True),
        ("under /E/CLOCKSPEED/.git", True),
        ("root is `<repo>` on E:", False),
        ("https://github.com/Remus3/Clockspeed", False),
        ("/srv/work/Clockspeed/Clockspeed", False),
    ],
    ids=["drive-backslash", "drive-slash", "git-bash", "git-bash-upper", "scrubbed", "url", "ci"],
)
def test_the_checkout_path_pattern_catches_every_spelling(text: str, *, hit: bool) -> None:
    """The guard's own mutation arm: each spelling of the checkout path is caught."""
    assert bool(ABSOLUTE_CHECKOUT_RE.search(text)) is hit


def test_no_absolute_checkout_path_in_the_audited_docs(repo_root: Path) -> None:
    for relative in AUDITED_DOCS:
        text = (repo_root / relative).read_text(encoding="utf-8")
        lines = [
            n for n, line in enumerate(text.splitlines(), 1) if ABSOLUTE_CHECKOUT_RE.search(line)
        ]
        assert not lines, f"{relative} spells an absolute checkout path on line(s) {lines}"
