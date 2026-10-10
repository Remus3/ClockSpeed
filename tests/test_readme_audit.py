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
import tomllib
from typing import TYPE_CHECKING, Final

from clockspeed.data import locate
from clockspeed.surface import config

if TYPE_CHECKING:
    from pathlib import Path

#: MAIN's stated budget: "README under ~220 lines".
README_LINE_BUDGET: Final = 220

#: A banner plus one dashboard screenshot.
ASSET_IMAGES: Final = 2

#: "a Quickstart of about 10 lines" - prose and command lines; fences and a
#: thematic break are layout, not lines of the Quickstart.
QUICKSTART_LINE_BUDGET: Final = 12

#: The PNG chunk types an image may carry. Everything else - tEXt, zTXt, iTXt,
#: eXIf, tIME and any private chunk - can hold text a renderer stamped in, so it
#: is refused rather than enumerated.
PNG_ALLOWED_CHUNKS: Final = frozenset(
    {b"IHDR", b"PLTE", b"tRNS", b"IDAT", b"IEND", b"sRGB", b"gAMA", b"cHRM", b"pHYs"}
)

PNG_SIGNATURE: Final = b"\x89PNG\r\n\x1a\n"

#: A drive-rooted spelling of the project folder, either slash, any case.
ABSOLUTE_CHECKOUT_RE: Final = re.compile(r"[A-Za-z]:[\\/]+Clockspeed", re.IGNORECASE)

#: The two docs the acceptance names, plus the two this item rewrote.
AUDITED_DOCS: Final = ("docs/LEDGER.md", "docs/history_notes.md", "README.md", "docs/OPERATIONS.md")

#: A Python-version-shaped token: 3.N or 3.NN not inside a longer number.
PY_VERSION_RE: Final = re.compile(r"(?<![\d.])3\.\d{1,2}(?![\d.])")

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
    banner = IMAGE_RE.search(text)
    assert banner is not None, "README.md shows no image"
    assert banner.start() < text.find("\n## "), "no banner above the first section"


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
    assert "](docs/OPERATIONS.md#" in sections["Quickstart"], "Quickstart links no install doc"


def test_env_var_table_lives_in_the_install_doc(repo_root: Path) -> None:
    readme = _readme(repo_root)
    operations = (repo_root / "docs" / "OPERATIONS.md").read_text(encoding="ascii")
    for name in ENV_OVERRIDES:
        row = f"| `{name}` |"
        assert row not in readme, f"README.md still carries the {name} row"
        assert row in operations, f"docs/OPERATIONS.md has no {name} row"


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


def test_no_absolute_checkout_path_in_the_audited_docs(repo_root: Path) -> None:
    for relative in AUDITED_DOCS:
        text = (repo_root / relative).read_text(encoding="utf-8")
        lines = [
            n for n, line in enumerate(text.splitlines(), 1) if ABSOLUTE_CHECKOUT_RE.search(line)
        ]
        assert not lines, f"{relative} spells an absolute checkout path on line(s) {lines}"
