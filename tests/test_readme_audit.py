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

import json
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

#: The README's dashboard screenshot.
DASHBOARD: Final = "docs/assets/dashboard.png"

#: Every path ``tools/sha_citation_binaries.json`` may pin. A pin admits a file the
#: SHA gate's decoder cannot read, and a compressed citation inside it is invisible
#: to the gate's byte grade, so the pin row's review is the only control: a new pin
#: is a reviewed change here as well as there.
PINNED_BINARIES: Final = frozenset({BANNER, DASHBOARD})
BINARY_PIN_FILE: Final = "tools/sha_citation_binaries.json"

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

#: A drive-rooted spelling of the project folder, any case, for any drive letter:
#: ``X:\Clockspeed`` or ``X:/Clockspeed``, drive-relative ``X:Clockspeed``, Git
#: Bash's ``/x/Clockspeed``, WSL's ``/mnt/x/`` and Cygwin's ``/cygdrive/x/``, an
#: admin share ``\\host\x$\Clockspeed`` with either slash, and the folder's 8.3
#: short name ``CLOCKS~<n>``.
ABSOLUTE_CHECKOUT_RE: Final = re.compile(
    r"(?:[A-Za-z]:[\\/]+|(?<!\w)[A-Za-z]:|(?<![\w.~/-])/[A-Za-z]/|/(?:mnt|cygdrive)/[A-Za-z]/"
    r"|[\\/]{2}[^\\/\s]+[\\/][A-Za-z]\$[\\/]+)Clockspeed|\bCLOCKS~\d",
    re.IGNORECASE,
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

#: Every spelling of the "no language model" claim this tree uses, any case:
#: ``language model`` and its plural, ``language-model``, one wrapped across a
#: line break, and ``LLM`` or ``LLMs``. No pattern reads text rendered into an
#: image's pixels; the banner's own footer is not README text.
LANGUAGE_MODEL_RE: Final = re.compile(r"\bLLMs?\b|\blanguage[-\s]+models?\b", re.IGNORECASE)

#: The heading the Quickstart links, and the one anchor GitHub gives it.
INSTALL_HEADING: Final = "### 1.2 Install and run from scratch"
INSTALL_ANCHOR: Final = "12-install-and-run-from-scratch"

#: Every prose paragraph the README's install section carried before CS-1292 moved
#: it into docs/OPERATIONS.md section 1.2, whitespace-collapsed, as section 1.2
#: holds it - the prerequisites list is one paragraph. Its fenced commands are
#: MOVED_COMMANDS; its "First result" paragraph is the README's, FIRST_RESULT.
MOVED_PROSE: Final = (
    "On a machine that has none of them yet, install from the official sources:",
    "1. **Python** from [python.org](https://www.python.org/downloads/windows/), in a "
    "release that meets the `requires-python` floor in "
    "[`pyproject.toml`](../pyproject.toml) - that file is where the version is pinned. "
    "That page lists the Python install manager first and the releases below it. Take a "
    'release\'s "Windows installer (64-bit)" rather than the install manager: the install '
    "manager refused to install on Windows 10 build 19041, where the installer worked. On"
    " the installer page that carries **Install Now**, tick **Add python.exe to PATH** "
    "before you click it - the box is unticked by default, and without it the `python "
    "--version` check below fails. [python.org's Windows "
    "guide](https://docs.python.org/3/using/windows.html) marks that installer deprecated"
    " from 3.14 and says it will not be produced for 3.16 or later. 2. **Git** from "
    "[git-scm.com](https://git-scm.com/download/win). The installer defaults are fine. 3."
    " **Node** from [nodejs.org](https://nodejs.org/), the LTS installer, only if you "
    "want the companion window or will run the test suite.",
    "Open a new terminal afterwards and check:",
    "`python --version` must print a version that meets `requires-python`. If it does "
    "not, `python` is not reaching a suitable install - follow python.org's official "
    "Windows guide, <https://docs.python.org/3/using/windows.html>, then re-run the "
    "check.",
    "Run every command below from the root of the clone, in the order given.",
    "**Two kinds of clone, two starting points.** If you only want to run Clockspeed, "
    "this section is the whole procedure and you can skip the rest of this file. If you "
    "will commit from the clone, do the virtual-environment step below, then run the "
    "bootstrap in section 1 above - it runs the same hook and environment commands as the"
    " next two steps here, plus the contributor tooling - and continue here at `python "
    "scripts/make_cert.py`.",
    "Create a virtual environment, activate it, and install the project with its `dev` extra:",
    "The activation line is the Windows `cmd` form; in Git Bash it is `source "
    ".venv/Scripts/activate`. A stock Windows PowerShell refuses it - running scripts is "
    "disabled under its default execution policy, and `python` then stays the base "
    "interpreter, so the install lands outside the virtual environment. In PowerShell, "
    "run this before the activation line; it lasts only for that terminal and changes no "
    "machine setting:",
    "`.venv/` is gitignored. The core itself has no runtime dependencies; the `dev` extra"
    " is the toolchain the next steps check for.",
    "Then:",
    "Points this clone's `core.hooksPath` at the tracked `.githooks/`. The next command "
    "counts that setting as a HARD dependency, so in a fresh clone it fails until this "
    "has run.",
    "Prints every dependency found and missing, split into HARD and SOFT. It exits "
    "non-zero only on a HARD one. A missing game or save is SOFT: it is reported and does"
    " not fail the check. Its `config/ports.json` row prints the dashboard's port.",
    "`scripts/make_cert.py` needs `openssl`. Git for Windows ships it in `<Git "
    "install>\\usr\\bin`, where `<Git install>` is the folder Git was installed into (`git "
    "--exec-path` prints a path that starts with it), but a default Git install does not "
    "put that folder on PATH, and the script then exits 1 saying openssl is not on PATH. "
    "Unless `openssl version` already answers, append the folder to PATH for this "
    "terminal first. In `cmd`:",
    'In PowerShell the same line is `$env:Path += ";<Git install>\\usr\\bin"`. Then:',
    "The dashboard is HTTPS only and will not start without a certificate pair. The pair "
    "is gitignored, so every fresh clone needs this once. Skip it and the next command "
    "exits 3 and says why.",
    "Starts the dashboard on the port recorded in `config/ports.json` - the entry under "
    "`allocations`, which `scripts/verify_env.py` also prints - bound to this machine "
    "only. With no arguments it finds the newest save on this machine and serves it. It "
    "prints nothing on startup, then logs one line per request, and keeps the terminal "
    "until you stop it.",
    "A machine with no save and no game still starts and still binds; the absence is "
    "reported as a status, not an error - `/api/health` reports the registry and the "
    "world as `absent`. If the port is taken the process exits and names it. No second "
    "port is ever tried.",
    "**A first ratio.** With a game installed, ask the solver for 30 Iron Ingot per "
    "minute from iron ore. The parameters travel in the query string of a POST; `-k` "
    "accepts the self-signed certificate and `-s` keeps curl's progress output out of the"
    " answer:",
    "Type `curl.exe`, not `curl`: in Windows PowerShell `curl` is an alias for "
    "`Invoke-WebRequest`, which refuses `-k`. `curl.exe` is the curl Windows ships, and "
    "the line runs unchanged in `cmd`.",
    "The answer lists each recipe with its exact machine count and the raw input per "
    'minute, every rate as a `{"num", "den"}` pair. `/api/registry` lists the item and '
    "recipe identifiers to ask about. Without a game there is no registry, and the route "
    "answers 503.",
    "The install, the save folder and the account folder beneath it are found "
    "automatically. To point Clockspeed somewhere else, set any of these environment "
    "variables before running the commands above:",
    "A variable naming a folder that does not exist is reported as not found; it does not"
    " fall back to automatic detection.",
    "To check that an override resolved, run `python scripts/verify_env.py`: each "
    "location row names the source it was resolved by, or reports it not found. The "
    "dashboard cannot tell you - an override pointing at an empty folder and no game at "
    "all both show there as no game installation found.",
)

#: The moved environment-variable table's rows, whole - a name alone survives a
#: row whose description was dropped.
MOVED_ROWS: Final = (
    "| `CLOCKSPEED_GAME_DIR` | The game install folder, such as `<your game folder>` |",
    "| `CLOCKSPEED_SAVE_ROOT` | The folder holding the account folders, such as "
    "`<your SaveGames folder>` |",
    "| `CLOCKSPEED_ACCOUNT_DIR` | The one account folder to read - a full path, or a folder "
    "name inside the save root |",
    "| `CLOCKSPEED_LOCAL_CONFIG` | A JSON file whose `game_dir`, `save_root` and "
    "`account_dir` keys are read when the matching variable is unset |",
    "| `CLOCKSPEED_CERT_DIR` | The folder holding the dashboard's certificate pair, instead "
    "of `certs/` in the clone. `scripts/make_cert.py` writes there and the dashboard reads "
    "there; `--cert-dir` beats it |",
    "| `CLOCKSPEED_DASHBOARD_PORT` | The port the dashboard binds, instead of the recorded "
    "one; `--port` beats it |",
)

#: The first result, which the README owns (the CS-1292 DECISION RECORD,
#: decision 2) under its own ``## First result`` heading.
FIRST_RESULT_HEADING: Final = "First result"
FIRST_RESULT_ANCHOR: Final = "first-result"
FIRST_RESULT: Final = (
    "Open `https://localhost:<port>/`, where `<port>` is the `allocations` entry in "
    "`config/ports.json` that `scripts/verify_env.py` prints. The certificate is "
    "self-signed and your system does not trust it, so the browser shows a certificate "
    'warning to accept before the page titled "Clockspeed dashboard" loads. '
    "`https://localhost:<port>/api/health` answers a compact JSON object whose top-level "
    "`status` field is `ok`."
)

#: Phrases only the first result says; docs/OPERATIONS.md links it instead.
FIRST_RESULT_MARKERS: Final = (
    'the page titled "Clockspeed dashboard"',
    "top-level `status` field is `ok`",
    "a certificate warning to accept",
)

#: The ownership rows CS-1292 changed. ``CLAUDE.md`` section 4 owns them;
#: CONVENTIONS.md section 2 restates its table (drift guard (d) parses it), so
#: those rows must match; the doc-sync agent and the sync-docs command point at
#: ``CLAUDE.md`` section 4 and restate no row at all.
CHANGED_OWNER_ROWS: Final = ("README.md", "docs/OPERATIONS.md")
RESTATING_DOC: Final = "CONVENTIONS.md"
POINTING_DOCS: Final = (".claude/agents/doc-sync.md", ".claude/commands/sync-docs.md")
OWNER_ROW_RE: Final = re.compile(r"^\| `[^`]+` \|", re.MULTILINE)
#: The pointer itself. Both prompts also cite ``CLAUDE.md`` section 4 for an
#: unrelated rule, so the bare citation proves nothing; the pointer names the table.
OWNER_POINTER: Final = "the ownership table in `CLAUDE.md` section 4"

#: The tracked social preview is the one upload source; the gitignored card of
#: the same file name is not a copy of it, and no live doc names it.
GITIGNORED_CARD: Final = "data/social-preview.png"
CARD_DOCS: Final = ("docs/public-readiness.md", "README.md", "docs/OPERATIONS.md")


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


def _collapse(text: str) -> str:
    return " ".join(text.split())


def _paragraphs(markdown: str) -> set[str]:
    """Each blank-line-separated block outside fences and headings, whitespace collapsed."""
    found: set[str] = set()
    block: list[str] = []
    fenced = False
    for line in [*markdown.splitlines(), ""]:
        fence = line.startswith("```")
        if fence:
            fenced = not fenced
        if fence or fenced or not line.strip() or line.startswith("#"):
            if block:
                found.add(_collapse("\n".join(block)))
                block = []
            continue
        block.append(line)
    return found


def _owner_row(text: str, name: str) -> str | None:
    """The one ownership-table row naming ``name``, or None."""
    rows = [line for line in text.splitlines() if line.startswith(f"| `{name}` |")]
    assert len(rows) <= 1, f"{len(rows)} ownership rows name {name}"
    return rows[0] if rows else None


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


@pytest.mark.parametrize(
    ("text", "hit"),
    [
        ("No language model computes it", True),
        ("| **Language models** | None |", True),
        ("an LLM-backed explainer", True),
        ("a language-model ranker", True),
        ("NO LANGUAGE MODEL IN THE ADVICE PATH", True),
        ("contains no language\nmodel", True),
        ("no LLM in the advice path", True),
        ("two LLMs", True),
        ("an llm", True),
        ("the language of the model", False),
        ("LLMNR lookups", False),
        ("a modelled language", False),
    ],
    ids=[
        "plain",
        "plural",
        "llm-hyphen",
        "hyphen",
        "upper",
        "wrapped",
        "no-llm",
        "llms",
        "lower-llm",
        "apart",
        "longer-word",
        "reversed",
    ],
)
def test_the_language_model_pattern_catches_every_spelling(text: str, *, hit: bool) -> None:
    """The guard's own mutation arm: each spelling the tree uses is caught."""
    assert bool(LANGUAGE_MODEL_RE.search(text)) is hit


def test_language_model_is_named_only_in_at_a_glance(repo_root: Path) -> None:
    hits = {
        name: len(LANGUAGE_MODEL_RE.findall(body))
        for name, body in _sections(_readme(repo_root)).items()
    }
    assert hits.get("At a glance", 0) == 1, "At a glance must name it exactly once"
    elsewhere = {name or "(preamble)": n for name, n in hits.items() if n and name != "At a glance"}
    assert not elsewhere, f"also named in {elsewhere}"


def test_citation_leaves_the_language_model_claim_to_the_readme(repo_root: Path) -> None:
    """MAIN's item 4 counts CITATION.cff as one more repetition of the claim."""
    cff = (repo_root / "CITATION.cff").read_text(encoding="ascii")
    assert not LANGUAGE_MODEL_RE.search(cff), "CITATION.cff repeats it"


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
    linked = re.findall(r"\]\(docs/OPERATIONS\.md(?:#([^)\s]*))?\)", quickstart)
    assert linked == [INSTALL_ANCHOR], f"Quickstart links docs/OPERATIONS.md at {linked}"
    operations = _operations(repo_root)
    headings = [line for line in operations.splitlines() if re.match(r"#{1,6} ", line)]
    taking = [
        h for h in headings if doc_sweep.Slugger().slug(h.lstrip("#").strip()) == INSTALL_ANCHOR
    ]
    assert taking == [INSTALL_HEADING], f"heading(s) slugged {INSTALL_ANCHOR}: {taking}"
    landed = doc_sweep.anchors(operations)
    assert INSTALL_ANCHOR in landed, f"{INSTALL_ANCHOR} resolves to no anchor"
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


def test_section_1_2_holds_every_moved_paragraph(repo_root: Path) -> None:
    """Every prose paragraph and table row the install section carried is in section 1.2."""
    section = _subsection(_operations(repo_root), INSTALL_HEADING)
    held = _paragraphs(section)
    missing = [n for n, paragraph in enumerate(MOVED_PROSE) if _collapse(paragraph) not in held]
    assert not missing, f"section 1.2 lacks moved paragraph(s) {missing} of MOVED_PROSE"
    lines = section.splitlines()
    rows = [n for n, row in enumerate(MOVED_ROWS) if row not in lines]
    assert not rows, f"section 1.2 lacks moved table row(s) {rows} of MOVED_ROWS"


def test_the_first_result_lives_in_the_readme_alone(repo_root: Path) -> None:
    """README owns the first result; docs/OPERATIONS.md links it and restates none of it."""
    readme = _readme(repo_root)
    body = _sections(readme).get(FIRST_RESULT_HEADING)
    assert body is not None, f"README.md has no '## {FIRST_RESULT_HEADING}' section"
    assert FIRST_RESULT in _paragraphs(body), "README's first result is not FIRST_RESULT"
    assert FIRST_RESULT_ANCHOR in doc_sweep.anchors(readme), "no first-result anchor"
    operations = _operations(repo_root)
    section = _subsection(operations, INSTALL_HEADING)
    assert f"](../README.md#{FIRST_RESULT_ANCHOR})" in section, "section 1.2 does not link it"
    flat = _collapse(operations)
    restated = [marker for marker in FIRST_RESULT_MARKERS if marker in flat]
    assert not restated, f"docs/OPERATIONS.md restates the first result: {restated}"


def test_conventions_restates_the_changed_owner_rows_as_claude_md_owns_them(
    repo_root: Path,
) -> None:
    claude = (repo_root / "CLAUDE.md").read_text(encoding="utf-8")
    restated = (repo_root / RESTATING_DOC).read_text(encoding="utf-8")
    for name in CHANGED_OWNER_ROWS:
        owner = _owner_row(claude, name)
        assert owner is not None, f"CLAUDE.md section 4 has no {name} row"
        assert _owner_row(restated, name) == owner, f"{RESTATING_DOC}'s {name} row differs"


@pytest.mark.parametrize("relative", POINTING_DOCS)
def test_the_doc_sync_prompts_point_at_the_owner_table(repo_root: Path, relative: str) -> None:
    text = (repo_root / relative).read_text(encoding="utf-8")
    rows = [text.count("\n", 0, m.start()) + 1 for m in OWNER_ROW_RE.finditer(text)]
    assert not rows, f"{relative} restates ownership row(s) on line(s) {rows}"
    assert OWNER_POINTER in _collapse(text), f"{relative} does not point at the owner table"


@pytest.mark.parametrize("relative", CARD_DOCS)
def test_no_live_doc_names_the_gitignored_card(repo_root: Path, relative: str) -> None:
    text = (repo_root / relative).read_text(encoding="utf-8")
    assert GITIGNORED_CARD not in text, f"{relative} names {GITIGNORED_CARD}"


def test_the_readiness_doc_uploads_the_tracked_banner(repo_root: Path) -> None:
    text = _collapse((repo_root / "docs" / "public-readiness.md").read_text(encoding="utf-8"))
    assert f"Upload `{BANNER}`" in text, "the upload step does not name the tracked banner"


def test_the_binary_pins_name_only_the_readme_images(repo_root: Path) -> None:
    pins = json.loads((repo_root / BINARY_PIN_FILE).read_bytes().decode("ascii"))
    assert set(pins) == PINNED_BINARIES, f"{BINARY_PIN_FILE} pins {sorted(pins)}"


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
        ("`ls /mnt/e/Clockspeed/docs`", True),
        ("`cd /cygdrive/E/Clockspeed`", True),
        ("drive-relative E:Clockspeed\\docs", True),
        ("the short name E:\\CLOCKS~1\\docs", True),
        ("CLOCKS~2", True),
        ("\\\\localhost\\e$\\Clockspeed\\docs", True),
        ("//localhost/E$/Clockspeed/docs", True),
        ("root is `<repo>` on E:", False),
        ("https://github.com/Remus3/Clockspeed", False),
        ("/srv/work/Clockspeed/Clockspeed", False),
        ("Project:Clockspeed", False),
        ("`git show HEAD~1`", False),
    ],
    ids=[
        "drive-backslash",
        "drive-slash",
        "git-bash",
        "git-bash-upper",
        "wsl",
        "cygwin",
        "drive-relative",
        "short-name",
        "short-name-bare",
        "unc-admin-share",
        "unc-forward-slashes",
        "scrubbed",
        "url",
        "ci",
        "label-colon",
        "git-ancestry",
    ],
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
