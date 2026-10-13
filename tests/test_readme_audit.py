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

import codecs
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tomllib
from collections import Counter
from pathlib import Path
from typing import Final

import pytest

from clockspeed.data import locate
from clockspeed.surface import config

_TOOLS_DIR: Final = Path(__file__).resolve().parents[1] / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import doc_sweep  # noqa: E402
import sha_citation_gate  # noqa: E402

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

#: One path separator - a slash or a backslash - raw, URL-encoded or as an HTML
#: entity (``%5C``, ``%2F``, ``&#92;``, ``&#x5C;``, ``&bsol;``, ``&sol;``), a JSON-escaped
#: slash, or a ``\u`` or ``\x`` escape of either (CS-1308) - an escape's backslash also
#: doubled, as a string literal in code writes it. The group is atomic (CS-1308 fix round
#: 4): it keeps the first alternative that matches and never splits that text again, so a
#: JSON-escaped slash is one separator, never a backslash and then a slash, and a run of
#: them cannot backtrack exponentially. So the escapes come first, then the JSON-escaped
#: slash, then the bare backslash.
_SEP: Final = (
    r"(?>\\+u005c|\\+x5c|\\+u002f|\\+x2f|\\*/|\\|%5c|%2f|&#0*92;|&#0*47;|&#x0*5c;"
    r"|&#x0*2f;|&bsol;|&sol;)"
)

#: A drive colon, raw, URL-encoded, as an HTML entity, or as a ``\u`` or ``\x`` escape.
_COLON: Final = r"(?::|%3a|&#0*58;|&#x0*3a;|&colon;|\\+u003a|\\+x3a)"

#: An admin share's dollar sign, raw, URL-encoded or as an HTML entity.
_DOLLAR: Final = r"(?:\$|%24|&#0*36;|&#x0*24;|&dollar;)"

#: A short name's tilde, raw, URL-encoded or as an HTML entity.
_TILDE: Final = r"(?:~|%7e|&#0*126;|&#x0*7e;)"

#: One or more separators, each optionally after a ``.`` or ``..`` segment.
_DOTTED: Final = rf"(?:\.{{0,2}}{_SEP})+"

#: The left edge of a drive-relative spelling: no ASCII letter or digit before it, so an
#: underscore or other punctuation glued in front does not block a match (CS-1308).
_EDGE: Final = r"(?<![A-Za-z0-9])"

#: A single-letter option glued in front - ``-C``, ``-e``, ``-I`` - itself at an edge.
_GLUED: Final = rf"(?<={_EDGE}-[A-Za-z])"

#: A drive-rooted spelling of the project folder, any case, for any drive letter:
#: ``X:\Clockspeed`` or ``X:/Clockspeed``, with ``.`` and ``..`` segments
#: (``X:.\``, ``X:\.\``), drive-relative ``X:Clockspeed``, Git Bash's
#: ``/x/Clockspeed``, WSL's ``/mnt/x/`` and Cygwin's ``/cygdrive/x/``, an admin share
#: ``x$`` behind any prefix (``\\host\``, ``\\?\UNC\host\``, ``\\.\UNC\host\``), a
#: ``\\?\Volume{<guid>}\`` path, and the folder's 8.3 short name ``CLOCKS~<n>`` -
#: every separator, colon, dollar and tilde also URL-encoded or as an HTML entity.
#: CS-1308: Git Bash's form also JSON-escaped; a Git Bash, WSL or Cygwin form with
#: repeated separators and ``.`` or ``..`` segments after its drive letter, as the drive
#: form takes them, and a WSL or Cygwin form with them before it too; a drive-relative
#: or Git Bash form behind an underscore or a glued single-letter option; a Git Bash form
#: behind a hyphen, as bash's ``${X-...}`` and ``${X:-...}`` defaults write it, or led by
#: two or three separators, as MSYS's double slash and a file URI's empty authority write
#: it; and the short name behind anything but a letter, so ``-CLOCKS~1`` is read and
#: ``overclocks~150%`` is not.
ABSOLUTE_CHECKOUT_RE: Final = re.compile(
    rf"(?:[A-Za-z]{_COLON}{_DOTTED}|(?:{_EDGE}|{_GLUED})[A-Za-z]{_COLON}"
    rf"|(?:(?<![A-Za-z0-9.~/\\])|{_GLUED}){_SEP}{{1,3}}[A-Za-z]{_DOTTED}"
    rf"|{_SEP}(?:mnt|cygdrive){_DOTTED}[A-Za-z]{_DOTTED}"
    rf"|{_SEP}[A-Za-z]{_DOLLAR}{_DOTTED}|{_SEP}Volume\{{[0-9A-Fa-f-]+\}}{_DOTTED})"
    rf"Clockspeed|(?<![A-Za-z])CLOCKS{_TILDE}\d",
    re.IGNORECASE,
)

#: The two docs the acceptance names, plus the two this item rewrote.
AUDITED_DOCS: Final = ("docs/LEDGER.md", "docs/history_notes.md", "README.md", "docs/OPERATIONS.md")

#: A Python-version-shaped token, whole: 3.N or 3.NN plus any further ``.N`` parts
#: and an optional ``.x`` wildcard, so ``3.13.0`` and ``3.14.x`` are each one token
#: and never equal the floor ``3.13``. A sentence's closing period ends a token; it
#: does not hide it.
PY_VERSION_RE: Final = re.compile(r"(?<![\d.])3\.\d{1,2}(?:\.\d+)*(?:\.x)?(?!\w|\.\d)")

#: ``requires-python`` as a closed range of minors, floor AND ceiling (CS-G03). A bare
#: floor admitted python.org's newest release, 3.15.0, which the ``dev`` extra could
#: not install on: PyYAML shipped no wheel for it and its source build needs MSVC.
REQUIRES_PYTHON_RE: Final = re.compile(r">=3\.(\d{1,2}),<3\.(\d{1,2})")

#: The trove classifier prefix naming one supported minor.
PY_CLASSIFIER: Final = "Programming Language :: Python :: "

#: A doc admitting every release above a version - the phrase that sent a fresh
#: walker to python.org's newest release.
OPEN_CEILING_RE: Final = re.compile(
    r"(?<![\d.])3\.\d{1,2}(?:\.\d+)*\s+or\s+(?:newer|higher|above)\b", re.IGNORECASE
)

#: The two docs that tell a reader which Python to install.
PYTHON_DOCS: Final = ("README.md", "docs/OPERATIONS.md")

#: The Quickstart lines a stock Windows PowerShell needs, each paired with the
#: Quickstart command it must come before (CS-G03): activation is refused under
#: the default execution policy, and make_cert exits 1 with no openssl on PATH.
QUICKSTART_ORDER: Final = (
    (
        "Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force",
        ".venv\\Scripts\\activate",
    ),
    ('$env:Path += ";<Git install>\\usr\\bin"', "python scripts/make_cert.py"),
)

#: How a doc says where ``<Git install>`` ends in the path ``git --exec-path``
#: prints: Git for Windows puts its binaries under one of these (CS-G03).
GIT_INSTALL_MARKERS: Final = ("`/mingw64/`", "`/ucrt64/`")

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
    "1. **Python** 3.13 or 3.14 - take the newest 3.14.x - from "
    "[python.org](https://www.python.org/downloads/windows/). The supported range is "
    "`requires-python` in [`pyproject.toml`](../pyproject.toml), and python.org's newest "
    "release can lie above it. The download page lists the Python install manager first "
    "and the releases below it. Take a "
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
    "`python --version` must print a version inside the `requires-python` range. If it "
    "does not, `python` is not reaching a suitable install - follow python.org's official "
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
    "install>\\usr\\bin`, where `<Git install>` is the folder Git was installed into - the "
    "part before `/mingw64/` or `/ucrt64/` in the path `git --exec-path` prints - but a "
    "default Git install does not put that folder on PATH, and the script then exits 1 "
    "saying openssl is not on PATH. "
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


def _supported_pythons(repo_root: Path) -> list[str]:
    """Every minor ``requires-python`` admits, oldest first, from its floor and ceiling."""
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    spec = "".join(pyproject["project"]["requires-python"].split())
    match = REQUIRES_PYTHON_RE.fullmatch(spec)
    assert match, f"requires-python {spec!r} is not a closed >=3.N,<3.M range"
    low, high = int(match[1]), int(match[2])
    assert low < high, f"requires-python {spec!r} admits no minor"
    return [f"3.{minor}" for minor in range(low, high)]


def _range_phrase(supported: list[str]) -> str:
    """The words a doc states the range in: ``3.13 or 3.14``, newest last."""
    if len(supported) == 1:
        return supported[0]
    return f"{', '.join(supported[:-1])} or {supported[-1]}"


@pytest.mark.parametrize(
    ("text", "tokens"),
    [
        ("3.13 or 3.14", ["3.13", "3.14"]),
        ("take the newest 3.14.x.", ["3.14.x"]),
        ("it found 3.13.0.", ["3.13.0"]),
        ("Python 3.13.", ["3.13"]),
        ("section 13.3.14 and v23.14", []),
    ],
)
def test_the_python_version_pattern_reads_whole_tokens(text: str, tokens: list[str]) -> None:
    """The guard's own mutation arm: a wildcard or a sentence end hides no token."""
    assert PY_VERSION_RE.findall(text) == tokens


@pytest.mark.parametrize(
    ("text", "hit"),
    [
        ("3.13 or newer", True),
        ("Python 3.13.0 or\nhigher", True),
        ("3.13 or 3.14", False),
        ("not be produced for 3.16 or later", False),
    ],
)
def test_the_open_ceiling_pattern_catches_the_walk_phrase(text: str, *, hit: bool) -> None:
    """The guard's own mutation arm: the phrase the docs carried before CS-G03 is caught."""
    assert bool(OPEN_CEILING_RE.search(text)) is hit


def test_requires_python_has_a_ceiling_the_classifiers_match(repo_root: Path) -> None:
    """A bare floor let a fresh walker take a release the ``dev`` extra cannot install on."""
    supported = _supported_pythons(repo_root)
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    minors = [
        item.removeprefix(PY_CLASSIFIER)
        for item in pyproject["project"]["classifiers"]
        if item.startswith(PY_CLASSIFIER + "3.")
    ]
    assert minors == supported, f"classifier minors {minors} differ from {supported}"


def test_python_version_is_stated_once_in_requirements(repo_root: Path) -> None:
    supported = _supported_pythons(repo_root)
    hits = {
        name: PY_VERSION_RE.findall(body)
        for name, body in _sections(_readme(repo_root)).items()
        if PY_VERSION_RE.search(body)
    }
    expected = [*supported, f"{supported[-1]}.x"]
    assert hits == {"Requirements": expected}, f"version tokens by section: {hits}"


@pytest.mark.parametrize("relative", PYTHON_DOCS)
def test_the_install_docs_state_the_pyproject_range(repo_root: Path, relative: str) -> None:
    """README and OPERATIONS name the range ``requires-python`` holds, and its newest minor."""
    supported = _supported_pythons(repo_root)
    text = _collapse((repo_root / relative).read_text(encoding="ascii"))
    stated = f"{_range_phrase(supported)} - take the newest {supported[-1]}.x"
    assert stated in text, f"{relative} does not say {stated!r}"
    open_ended = len(OPEN_CEILING_RE.findall(text))
    assert not open_ended, f"{relative} admits every newer release ({open_ended} hit(s))"


def test_the_quickstart_runs_on_a_stock_windows_powershell(repo_root: Path) -> None:
    """Each line a default PowerShell needs comes before the command that needs it."""
    quickstart = _sections(_readme(repo_root)).get("Quickstart", "")
    fenced = [
        line.split("  #")[0].strip()
        for block in re.findall(r"^```[^\n]*\n(.*?)^```", quickstart, re.MULTILINE | re.DOTALL)
        for line in block.splitlines()
        if line.strip()
    ]
    section = _subsection(_operations(repo_root), INSTALL_HEADING)
    for needed, before in QUICKSTART_ORDER:
        assert needed in fenced, f"the Quickstart lacks {needed!r}"
        assert before in fenced, f"the Quickstart lacks {before!r}"
        assert fenced.index(needed) < fenced.index(before), f"{needed!r} follows {before!r}"
        assert needed in section, f"section 1.2 does not explain {needed!r}"


def test_every_git_install_definition_says_where_it_ends(repo_root: Path) -> None:
    """``git --exec-path`` prints more than the install folder; say which part it is."""
    defined = [
        paragraph
        for paragraph in _paragraphs(_operations(repo_root))
        if "<Git install>" in paragraph and "`git --exec-path`" in paragraph
    ]
    assert defined, "docs/OPERATIONS.md never says how to find <Git install>"
    vague = [p for p in defined if not all(marker in p for marker in GIT_INSTALL_MARKERS)]
    assert not vague, f"{len(vague)} of {len(defined)} paragraph(s) leave <Git install> open-ended"


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
        ("\\\\?\\UNC\\host\\d$\\Clockspeed\\docs", True),
        ("\\\\.\\UNC\\host\\d$\\Clockspeed", True),
        ("\\\\?\\Volume{00000000-0000-0000-0000-000000000000}\\Clockspeed", True),
        ("drive-relative D:.\\Clockspeed\\docs", True),
        ("D:..\\Clockspeed", True),
        ("D:\\.\\Clockspeed", True),
        ("D:&#92;Clockspeed&#92;docs", True),
        ("D:&bsol;Clockspeed", True),
        ("D:&#x5C;Clockspeed", True),
        ("&#92;&#92;host&#92;d$&#92;Clockspeed", True),
        ("D%3A%5CClockspeed%5Cdocs", True),
        ("D:%5CClockspeed", True),
        ("file:///D%3A/Clockspeed/docs", True),
        ("D%3A%2FClockspeed", True),
        ("\\\\host\\d%24\\Clockspeed", True),
        ("CLOCKS%7E1", True),
        ('{"root": "\\/e\\/Clockspeed"}', True),
        ('"\\/mnt\\/e\\/Clockspeed"', True),
        ("git -C/e/Clockspeed status", True),
        ("git -C\\/e\\/Clockspeed status", True),
        ("x_CLOCKS~1", True),
        ("E:\\u005cClockspeed", True),
        ("E\\x3a\\x5cClockspeed", True),
        ("\\u002fe\\u002fClockspeed", True),
        ("cd /d//Clockspeed", True),
        ("cd /d/./Clockspeed", True),
        ("/mnt/d//Clockspeed", True),
        ("cd /mnt/./d/Clockspeed", True),
        ("gcc -e/d/Clockspeed", True),
        ("cc -I/d/Clockspeed/include", True),
        ("_/d/Clockspeed_", True),
        ("x_E:Clockspeed", True),
        ("-CLOCKS~1", True),
        ('"${CLOCKSPEED_ROOT:-/e/Clockspeed}"', True),
        ("${X-/e/Clockspeed}", True),
        ("file:///e/Clockspeed", True),
        ("docker run -v //e/Clockspeed:/work", True),
        ("git -C//e/Clockspeed status", True),
        ("9CLOCKS~1", True),
        ("git -CE:Clockspeed status", True),
        ("-v \\/\\/e\\/Clockspeed:/work", True),
        ("root is `<repo>` on E:", False),
        ("https://github.com/Remus3/Clockspeed", False),
        ("/srv/work/Clockspeed/Clockspeed", False),
        ("Project:Clockspeed", False),
        ("Project&colon;Clockspeed", False),
        ("Project%3AClockspeed", False),
        ("https://example.invalid/a%2FClockspeed", False),
        ("`git show HEAD~1`", False),
        ('"x\\/b\\/Clockspeed"', False),
        ("Clockspeed~1", False),
        ("overclocks~150%", False),
        ("a-b/d/Clockspeed", False),
        ("https://example.com/e/Clockspeed-docs", False),
        ("a-b//d/Clockspeed", False),
        ("cd ./e/Clockspeed", False),
        ("cd ~/e/Clockspeed", False),
        ("cd v2/e/Clockspeed", False),
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
        "unc-long-path",
        "unc-device-path",
        "volume-guid",
        "drive-dot-relative",
        "drive-dotdot-relative",
        "drive-dot-segment",
        "html-decimal-backslash",
        "html-named-backslash",
        "html-hex-backslash",
        "html-unc",
        "url-colon-backslash",
        "url-backslash",
        "url-colon",
        "url-colon-slash",
        "url-dollar",
        "url-short-name",
        "json-escaped-git-bash",
        "json-escaped-wsl",
        "git-bash-glued-option",
        "json-escaped-glued-option",
        "short-name-glued",
        "unicode-escape-backslash",
        "hex-escape-colon-backslash",
        "unicode-escape-git-bash",
        "git-bash-doubled-separator",
        "git-bash-dot-segment",
        "wsl-doubled-separator",
        "wsl-dot-segment",
        "glued-option-e",
        "glued-option-i",
        "underscore-git-bash",
        "underscore-drive-relative",
        "short-name-after-dash",
        "bash-default-colon",
        "bash-default",
        "file-uri-git-bash",
        "msys-double-slash",
        "glued-option-double-slash",
        "short-name-after-digit",
        "glued-drive-relative",
        "json-escaped-double-slash",
        "scrubbed",
        "url",
        "ci",
        "label-colon",
        "label-colon-entity",
        "label-colon-url",
        "url-path-segment",
        "git-ancestry",
        "json-escaped-relative",
        "long-name-tilde",
        "overclock-percent",
        "hyphenated-relative",
        "url-single-letter-segment",
        "hyphenated-relative-double-slash",
        "dot-relative",
        "home-relative",
        "digit-segment",
    ],
)
def test_the_checkout_path_pattern_catches_every_spelling(text: str, *, hit: bool) -> None:
    """The guard's own mutation arm: each spelling of the checkout path is caught."""
    assert bool(ABSOLUTE_CHECKOUT_RE.search(text)) is hit


#: CS-1308 fix round 4 - the time one line of separators may take to search. The guard
#: reads every tracked line on every suite and CI run, so a pattern whose separator tokens
#: can split one text two ways - backtracking exponentially in the run's length - is a hang.
_BACKTRACK_BUDGET_S: Final = 0.25

#: The bound on the child that times the search: a pattern that backtracks without end is
#: killed there, and the arm fails, instead of the suite hanging.
_BACKTRACK_TIMEOUT_S: Final = 10

#: The runs the timing arm builds, 40 units each - JSON-escaped slashes, ``.`` segments and
#: the two interleaved - each then followed by a tail that completes no spelling.
_BACKTRACK_RUNS: Final = {
    "escaped-slashes": "\\/" * 40,
    "dot-segments": "/." * 40 + "/",
    "mixed": "\\/./" * 40,
}

#: The prefixes that lead a run into the drive, Git Bash and WSL branches of the pattern.
_BACKTRACK_PREFIXES: Final = ("E:", "/e", "/mnt")

#: The timing child: compiles the pattern it is sent and times one search per line.
_TIMING_CHILD: Final = """
import json, re, sys, time
spec = json.load(sys.stdin)
pattern = re.compile(spec["pattern"], spec["flags"])
rows = []
for line in spec["lines"]:
    start = time.perf_counter()
    hit = pattern.search(line) is not None
    rows.append([time.perf_counter() - start, hit])
print(json.dumps(rows))
"""


@pytest.mark.parametrize("kind", sorted(_BACKTRACK_RUNS))
def test_the_checkout_path_pattern_cannot_backtrack_catastrophically(kind: str) -> None:
    """Fix round 4: a 40-unit separator run and a tail that completes nothing search fast.

    Each line is searched in a child process killed after ``_BACKTRACK_TIMEOUT_S``, so a
    pattern that backtracks exponentially fails this arm rather than hanging the suite.
    """
    lines = [f"{prefix}{_BACKTRACK_RUNS[kind]}x" for prefix in _BACKTRACK_PREFIXES]
    spec = {
        "pattern": ABSOLUTE_CHECKOUT_RE.pattern,
        "flags": int(ABSOLUTE_CHECKOUT_RE.flags),
        "lines": lines,
    }
    try:
        done = subprocess.run(
            [sys.executable, "-I", "-c", _TIMING_CHILD],
            input=json.dumps(spec),
            capture_output=True,
            text=True,
            check=True,
            timeout=_BACKTRACK_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        pytest.fail(f"{kind}: the search did not finish within {_BACKTRACK_TIMEOUT_S} s")
    rows = json.loads(done.stdout)
    assert not any(hit for _, hit in rows), f"{kind}: a timing line matched, so it times nothing"
    slow = [round(seconds, 3) for seconds, _ in rows if seconds >= _BACKTRACK_BUDGET_S]
    assert not slow, f"{kind}: searches took {slow} s, over the {_BACKTRACK_BUDGET_S} s budget"


def test_no_absolute_checkout_path_in_the_audited_docs(repo_root: Path) -> None:
    for relative in AUDITED_DOCS:
        text = (repo_root / relative).read_text(encoding="utf-8")
        lines = [
            n for n, line in enumerate(text.splitlines(), 1) if ABSOLUTE_CHECKOUT_RE.search(line)
        ]
        assert not lines, f"{relative} spells an absolute checkout path on line(s) {lines}"


#: CS-1308 - the ruled kept set, pinned by line CONTENT; the session 137 decision record
#: in ``docs/LEDGER.md`` gives each line's reason. Per path, the SHA-256 of the full text,
#: newline stripped, of every line that spells the checkout root - the text fixes how
#: many spellings the line holds. An added, changed, moved or doubled spelling changes the
#: multiset; an edit that only shifts line numbers does not. The root is the operator's
#: chosen location, not personal data: these lines state it where the topology
#: (``CLAUDE.md`` section 2, ``BOOTSTRAP.md`` section 2), a settled entry (``CLAUDE.md``
#: section 7, ``BOOTSTRAP.md`` section 11) or the move's own record (ADR 0026) must, and
#: anywhere else a spelling is written ``<repo>`` in CS-1292's style. This file's own
#: pattern lines - the comment above the pattern, the mutation arm's cases and the planted
#: spellings - are kept the same way, line by line; the file itself is never exempt. A
#: digest that moves is a reviewed change to this table.
KEPT_CHECKOUT_LINES: Final[dict[str, tuple[str, ...]]] = {
    "BOOTSTRAP.md": (
        # section 2, the project-root row
        "653272d5dc9af6e07a1f4fa63c1b4bfe773dd3a6b98c181b3a03267711edfc8f",
        # section 11, the settled entry
        "bfc227c2eae7f1069667af8c8fef47ac0ba4ef324e178667614c68ae60626f04",
    ),
    "CLAUDE.md": (
        # section 2, the project-root line
        "42d5f6fc7e66bb738c3166f9f03e47f132628b5c39d61f9a5651f24d3e04c461",
        # section 7, the settled entry
        "19bd7c89374e3465c9eda1818a13682aeac972fc4ea549e97356a9ecc2df8481",
    ),
    "docs/adr/0026-the-root-moves-to-e.md": (
        # the old root and its reversal clause
        "0cd8b055635bf2706992c7f7f0ce8d125753f15723528d6870fa7639ca7cf898",
        # decision 1, the root
        "3c8dd2d49dcd4efb65532581dadf559f248cb953653f57b0fa228358de8358f1",
        # the copy of the whole root
        "a5f62a17c27c29afb62136200cd9c7876d208ea1e27ba9436d56effd9df4a744",
        # the old root held as a working directory
        "0ce9f2ed438915a402c460efbd806474a42f9a4a79428e21a93708af92322a16",
        # the old root recycled, the junction from it
        "abbe0f35037dbe1c1d3062ec0c10b5d4bd8ba9183731676b1f267d3221f5eb35",
        # the junction's target
        "8de51609b17b8d3424d990775a134e49fec3f061cc334c5e311aca929697a338",
        # where the lanes now land
        "526845ad38b6d39ef3b5d9c041a872dfa07207816fea80f793880b4af2061bc5",
    ),
    "tests/test_readme_audit.py": (
        # in file order: the pattern comment above ABSOLUTE_CHECKOUT_RE, every case of
        # the mutation arm that spells the root, then _PLANTED and _PLANTED_WSL
        "36155fe426789ec47d1b9f35957783384babb31373a83800fdccd500751495e4",
        "3c4e047afba7b7d6871cefd3b98103814891c1b859049b6a526d8883e92dcfe9",
        "ff6bd9dbb3aa0112afcaddac669eee1498db0a095ba96a6e3843d2fb2aee6505",
        "f2fb79c2ecd2c4abb381fef9f1ad273925bfbf05e373484c21eb8e5b0f545ecf",
        "c3dce4344007a7401292c713bac4b598553e89e2709960cdfe2b1c1e39257c94",
        "c85d103fc7fea652f89d57761bf62a19b0cb5de95c393d48b41552abb13e57ee",
        "e3275333f39fbfacbbfe1f3a013b61e371560d6a87c889618ee0e54e68dcd48f",
        "a765c10c2d3fe215a5624582cf6c49027a1da7c28847249e426c621ee845203a",
        "3e0b154fa853df327a6662daa98b4252a43658a4c4ff4387e093734b8c681e2c",
        "ae1b511a5406fd92194c1ad8fe9947213623936d0bb5d26f1a2373f2186456e3",
        "c5517dab387bfb7e9e1714fd5fe1e2b5a301d6e3cc143e78aa6f1345ba1b2943",
        "1064a3e15e34d629a0cb7d7714351e4e645725ed533671ebdd327cedb92c87cb",
        "d37e812dba81f09ba1018aff47b2eb26cc93cec76da6e53ee4154d377f2c0b14",
        "c8299ae6526a47e90a044063a4a65947278f8ebb1282655f9f6091c77188e1a8",
        "d03e485d9eb7e0e40f8dadc91d7533133ff8764b151fda642798ec6a864b3d4c",
        "4cf2e60fbfce1afe19dd340939cca050fc18b1c9a361e81f5ea92b44e1b7845e",
        "d993bcb2967ce7921faeadfdf800e5a4e0ccbdb5c501593b9ad3d61bc329761f",
        "f1960f6edc47b637c7184a22a9c5615f0b4dbfa40272fe8b8bcadc9eb4245103",
        "563986b106d28e14346c0e2b99e4ba8d8ea40a8a4d72666edbdd20a58aadb493",
        "ce93bb55a41b008346b1e709b891039e3dfb9683f57c42a4907bb59c4371de0f",
        "dcfbc7420da02c15dd9e9cdd1a68c37c652c9d183b6f2df4517d207a0ad911e6",
        "e718d3809f82495366d21ec589a50cf451a156965c31492faa7489e63a21032d",
        "9827f915757023e1fb3981cbc9165883dd2925217179f40521a6bdbe5309946e",
        "5710baac94e64651d087815eb814740126fd853c4488822027a88eb812e52cf8",
        "1805554f8ff4669176fe037fa988151d6b59d8f2efc37e1324f47a68e79c01fc",
        "ff7a95b1d8816a3abc3c763058841c5c902f91fabda4cc200afc17fe245c7ca0",
        "dd23da1b500a423d7e4b72387ac987885b59be297334e4ce53eece540a17bc8c",
        "b640e050a9176547cd20c2b50f59838db6f66b25f7d952c8ed03961cd86636c4",
        "464b9845899f3316f8e134489a5055ce340c8c442cf9de8fd12d4420856eb87d",
        "29a59663ecf73094df403d6eaf8a3f475b76bb9f82efeeae62a983c1edb601e1",
        "d781a501c2268385caa7e6823ce2f7bbf533d9e2574fda2cef651e96fba72a27",
        "8b494077970b22dba858319aea1b99e74dc208ce1d82cc262e3b7df952f6f455",
        "ea8cf6d31d4be854fb5dd00340ae6d0cab3a6d1f5a0f041c4bcea18becb8cedd",
        "9d9c18b5329f7acddba7f953793e50cbe1db87aef551167489fe659df404b647",
        "298a07aa90bbff722c3f9d650a5fbafd15f7c2dee5f3587cb512bff6ece58797",
        "d52d748fd02207812d8d0560f386ff2adc92114a43e658aa60384ea21f7521c6",
        "58c6c0b3d1aac22db6de9d6c0278b65c16864b9ff485d3bbb55483d90c5fdeb2",
        "60f66fa99149fe09fe3bd3d2c04e814f98d207163e377d8752e753d2513db538",
        "42bbaec604fb6810af26cc6019caad5a54e1596b38370ded4c0ee3b9a472d7da",
        "3d49b9659220e62d9b2c3fca517187b54d167b12e059f5cd778dbd1f6ed6b0ed",
        "bfb8bce76f3bc1dd563a3de14fb258771fd0496c41194a7fb8ed159a75d8f74c",
        "086bfb644abf96cc2763e85999fb67b2ee0d1145e0b50caf6276e497fb099ad8",
        "dac85b8d7186b7ef84b529276ad04805e8662057735630e0fc7e73febef709fe",
        "bb14c777623a1b22ecb345ea4a25c40df324ff2313600729118920f0a2bce9db",
        "cc010aa5383b83a6ab19dcb3e2051366335d5765887bb28f4204d41cca6a20fd",
        "a6b9ac6679369a07d99d815db788789ce41929b51163a78fcc1ae7a893d7a159",
        "5acb9f670c3ce5c9a0d34da320fbbe3c652f7d3308ebdbb326c160861c4e53a5",
        "8674602e485565d1b36140bb71e7775cb1c2c501a8208508b9e5b4488fd81165",
        "2e2017689751b56205872f7540b3dbcb8c8659980c984354cfa89fa2907b25be",
        "0b7c9d18dbda419dbf4c50ec8ba2529a164b5858c0e8d1e5cebf5f1496250402",
        "95b35543fd6f41acb481d69c318d5316f22c68cd5d72d8705940e9733075d4a6",
        "c039a28e95cd731434b1d9f3a7ad4037d2f418350f08db26195bec94e8225945",
        "8da99a651634e608d3622a594dbd87cffe39226da6c84952821f3b15efa0fef9",
        "784f1bda615899afb126837776908f751e0ac1f7d7d15c82dd6ceaea510e96ee",
        "0b65029b0c925c77a89fb71f5e03e13a42e4f9eaf70b30603941b647a23f01db",
        "d0d4438f007929c56ed1de3602e186f3a51f5057c1b3c21a9d99a1951c8cefc5",
        "918f5d4c66a6e4ff427f8769be9fc80e5fb70e3b1829e24b8db3efe0b4888c7b",
        "d34ba214fd2a6d3219adad39a5dc60fb2bcbcfc212f5a2d4080ecaf59d43210a",
    ),
}

#: Git variables that would point a child process at another repository's state.
_GIT_REDIRECTS: Final = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE",
)

#: The index mode of a symlink: its blob is the link's text, which git publishes.
_SYMLINK_MODE: Final = "120000"

#: The index mode of a gitlink: it names a commit of another repository, and a commit id
#: is hexadecimal, which cannot spell the root.
_GITLINK_MODE: Final = "160000"

#: The fields of one ``git ls-files -s`` entry before its tab: mode, blob id, stage.
_INDEX_FIELDS: Final = 3


def _git_env() -> dict[str, str]:
    """This process's environment without the variables that redirect git elsewhere."""
    return {name: value for name, value in os.environ.items() if name not in _GIT_REDIRECTS}


#: The byte-order marks that make the path guard also read a file as UTF-16 and UTF-32.
_WIDE_BOMS: Final = (
    codecs.BOM_UTF32_LE,
    codecs.BOM_UTF32_BE,
    codecs.BOM_UTF16_LE,
    codecs.BOM_UTF16_BE,
)

#: The wide codecs a NUL-bearing or BOM-marked file is also read as, with each code unit.
_WIDE_CODECS: Final = (("utf-16-le", 2), ("utf-16-be", 2), ("utf-32-le", 4), ("utf-32-be", 4))


def _wide_reads(data: bytes, errors: str) -> list[str]:
    """``data`` read as UTF-16 and UTF-32, both byte orders, at every alignment.

    Under ``errors="strict"`` a read that does not decode is dropped; under ``"replace"``
    every read decodes, each undecodable code unit becoming U+FFFD.
    """
    reads: list[str] = []
    for codec, width in _WIDE_CODECS:
        for offset in range(width):
            body = data[offset:]
            try:
                reads.append(body[: len(body) - len(body) % width].decode(codec, errors))
            except UnicodeDecodeError:
                continue
    return reads


def _decodings(data: bytes) -> list[str] | None:
    """Every view of one body the path guard reads, or None when the body is unscannable.

    A body is SCANNABLE when strict UTF-8 decodes it or, if it carries a NUL or a UTF-16
    or UTF-32 byte-order mark, when a strict UTF-16 or UTF-32 read does in either byte
    order at some alignment. Only that judgment is strict; a scannable body is read as:

    - its strict UTF-8 text, or its bytes as latin-1 when strict UTF-8 refuses them;
    - if it carries a NUL or a wide byte-order mark, also its bytes with every NUL
      removed, as latin-1 - the view the SHA citation gate's unread-file grade takes,
      repeated here because that grade is private to the gate and scans for its own
      pattern - and a lenient (``errors="replace"``) UTF-16 and UTF-32 read in both byte
      orders at every alignment.

    What that guarantees, and no more: an ASCII spelling whose characters are separated
    only by NULs is read joined, and a spelling written in UTF-16 or UTF-32 code units is
    read at its own alignment even inside bytes no strict wide read decodes. Removing the
    NULs also joins the spelling's neighbours, so a letter separated from its left edge
    only by NULs blocks the pattern's edge checks as if written glued. An encoding none of
    these views names - compression, base64, an octal escape - is not read at all.
    """
    try:
        views = [data.decode("utf-8")]
    except UnicodeDecodeError:
        views = []
    wide = b"\0" in data or data.startswith(_WIDE_BOMS)
    if not views and not (wide and _wide_reads(data, "strict")):
        return None
    if not views:
        views.append(data.decode("latin-1"))
    if wide:
        views.append(data.replace(b"\0", b"").decode("latin-1"))
        views.extend(_wide_reads(data, "replace"))
    return views


def _line_digest(line: str) -> str:
    """The SHA-256 of one line's full text, the kept table's key."""
    return hashlib.sha256(line.encode("utf-8", "surrogatepass")).hexdigest()


def _index_entries(repo_root: Path) -> dict[str, list[tuple[str, str]]]:
    """Each tracked path's index entries as (mode, blob id), every stage, in index order."""
    listed = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "-s", "-z"],
        env=_git_env(),
        check=True,
        capture_output=True,
        timeout=120,
    )
    entries: dict[str, list[tuple[str, str]]] = {}
    for record in listed.stdout.split(b"\0"):
        meta, _, name = record.partition(b"\t")
        fields = meta.decode("ascii").split()
        if name and len(fields) == _INDEX_FIELDS:
            path = name.decode("utf-8", "replace")
            entries.setdefault(path, []).append((fields[0], fields[1]))
    return entries


def _index_blob(repo_root: Path, oid: str) -> bytes | None:
    """One blob's bytes from the object store, or None when git does not answer them."""
    shown = subprocess.run(
        ["git", "-C", str(repo_root), "cat-file", "blob", oid],
        env=_git_env(),
        check=False,
        capture_output=True,
        timeout=120,
    )
    return shown.stdout if shown.returncode == 0 else None


def _tracked_bodies(
    repo_root: Path, relative: str, entries: list[tuple[str, str]]
) -> list[bytes] | None:
    """Every distinct body of one tracked path, or None when one of them cannot be read.

    A symlink entry's body is its blob - the link text git publishes - and the link is
    never followed, whether or not anything sits at the path. A gitlink has no body. Any
    other entry is read from the work tree, or from its index blob when the work tree
    has no file there; any other read error leaves the path unscannable, never skipped.
    A path the index does not list is unscannable too.
    """
    if not entries:
        return None
    bodies: list[bytes] = []
    for mode, oid in entries:
        if mode == _GITLINK_MODE:
            continue
        body: bytes | None
        if mode == _SYMLINK_MODE:
            body = _index_blob(repo_root, oid)
        else:
            try:
                body = (repo_root / relative).read_bytes()
            except FileNotFoundError:
                body = _index_blob(repo_root, oid)
            except OSError:
                body = None
        if body is None:
            return None
        if body not in bodies:
            bodies.append(body)
    return bodies


def _body_hits(relative: str, bodies: list[bytes], pins: dict[str, str]) -> Counter[str] | None:
    """One path's multiset of matching-line digests, or None when a body is unscannable.

    The multiset is the elementwise maximum over the bodies and their views, so a line
    two views both carry counts once and a line one view carries twice counts twice. A
    body whose path AND bytes match a CS-1292 pin is skipped.
    """
    hits: Counter[str] = Counter()
    for body in bodies:
        if sha_citation_gate.is_known_binary(relative, body, pins):
            continue
        views = _decodings(body)
        if views is None:
            return None
        for view in views:
            lines = view.splitlines()
            hits |= Counter(_line_digest(x) for x in lines if ABSOLUTE_CHECKOUT_RE.search(x))
    return hits


def _checkout_path_hits(repo_root: Path) -> tuple[dict[str, Counter[str]], list[str]]:
    """Each tracked path's multiset of matching-line digests, and the paths nothing reads.

    Only a body whose path AND bytes match a CS-1292 pin in
    ``tools/sha_citation_binaries.json`` is skipped, read through the SHA citation gate's
    own loader rather than a copy of it. The text lives only in this frame and the two
    helpers, so a failing assertion's locals never carry a matched line.
    """
    pins = sha_citation_gate.load_known_binaries(repo_root)
    index = _index_entries(repo_root)
    found: dict[str, Counter[str]] = {}
    unscannable: list[str] = []
    for relative in doc_sweep.tracked_files(repo_root):
        bodies = _tracked_bodies(repo_root, relative, index.get(relative, []))
        hits = None if bodies is None else _body_hits(relative, bodies, pins)
        if hits is None:
            unscannable.append(relative)
        elif hits:
            found[relative] = hits
    return found, unscannable


def _kept_set_problems(found: dict[str, Counter[str]]) -> list[str]:
    """One ``<path>: <n> unexpected, <n> missing`` line per path off the kept table."""
    problems: list[str] = []
    for relative in sorted(set(found) | set(KEPT_CHECKOUT_LINES)):
        have = found.get(relative, Counter())
        want = Counter(KEPT_CHECKOUT_LINES.get(relative, ()))
        unexpected = sum((have - want).values())
        missing = sum((want - have).values())
        if unexpected or missing:
            problems.append(f"{relative}: {unexpected} unexpected, {missing} missing")
    return problems


def test_no_absolute_checkout_path_in_any_tracked_text_file(repo_root: Path) -> None:
    """CS-1308 - the CS-1292 path guard over every tracked file, against the kept table.

    Every tracked path is read, this file included; only the hash-pinned binaries are
    not. A path that cannot be read or decoded fails as unscannable. The messages name
    paths and counts of line digests only, never a matched line, because the matched
    text is what is scrubbed.
    """
    found, unscannable = _checkout_path_hits(repo_root)
    assert not unscannable, (
        f"tracked paths the guard cannot read or decode (unscannable): {unscannable}"
    )
    problems = _kept_set_problems(found)
    assert not problems, (
        "the checkout root is spelled off the kept table (path: line digests): "
        + "; ".join(problems)
    )


# --- CS-1308 fix round 1: the whole-tree guard, mutated in a planted tree ---------
#
# Each arm below plants one mutation the session 137 acceptance adversary showed
# surviving, in a synthetic work tree that tracks byte-copies of the ruled kept files,
# and calls the whole-tree guard on it. A planted tree that is the kept files alone is
# green, so a red arm is red for its one mutation; each arm also checks the failure
# names the mutated path.

#: The files a planted tree copies byte for byte from the real one: every file the
#: ruled kept set touches, so the kept table holds there exactly as it does here.
_PLANTED_FROM: Final = (
    "BOOTSTRAP.md",
    "CLAUDE.md",
    "docs/adr/0026-the-root-moves-to-e.md",
    "tests/test_readme_audit.py",
)

#: The spelling a planted arm writes - one of the guard's own pattern lines.
_PLANTED: Final = "D:\\Clockspeed"

#: The WSL form the moved-spelling arm writes - one of the guard's own pattern lines.
_PLANTED_WSL: Final = "/mnt/d/Clockspeed"


def _planted_tree(
    repo_root: Path,
    tmp_path: Path,
    files: dict[str, bytes],
    index_only: dict[str, tuple[str, bytes]] | None = None,
) -> Path:
    """A synthetic work tree tracking byte-copies of the kept files, then ``files`` over them.

    Each ``index_only`` entry - path to (index mode, blob bytes) - is then written into
    the index alone, over any entry ``files`` gave that path, with no work-tree change:
    a symlink entry git records on a checkout that writes no link, for one.
    """
    root = tmp_path / "planted"
    for relative in _PLANTED_FROM:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo_root / relative, target)
    for relative, data in files.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    env = _git_env()
    env["GIT_CONFIG_GLOBAL"] = str(tmp_path / "absent" / "gitconfig-global")
    env["GIT_CONFIG_SYSTEM"] = str(tmp_path / "absent" / "gitconfig-system")
    for args in (("init", "-q"), ("add", "-A")):
        subprocess.run(
            ["git", *args], cwd=root, env=env, check=True, capture_output=True, timeout=60
        )
    for relative, (mode, data) in (index_only or {}).items():
        stored = subprocess.run(
            ["git", "hash-object", "-w", "--stdin"],
            cwd=root,
            env=env,
            input=data,
            check=True,
            capture_output=True,
            timeout=60,
        )
        oid = stored.stdout.decode("ascii").strip()
        subprocess.run(
            ["git", "update-index", "--add", "--cacheinfo", f"{mode},{oid},{relative}"],
            cwd=root,
            env=env,
            check=True,
            capture_output=True,
            timeout=60,
        )
    return root


def _kept_lines(repo_root: Path, relative: str) -> tuple[list[str], int]:
    """A kept file's lines, and the index of its first line that spells the root."""
    lines = (repo_root / relative).read_bytes().decode("utf-8").split("\n")
    index = next(n for n, line in enumerate(lines) if ABSOLUTE_CHECKOUT_RE.search(line))
    return lines, index


def _guard_failure(root: Path) -> str:
    """The whole-tree guard's failure message on ``root``; the arm fails if it passes."""
    with pytest.raises(AssertionError) as caught:
        test_no_absolute_checkout_path_in_any_tracked_text_file(root)
    return str(caught.value)


def test_a_planted_tree_of_the_kept_files_alone_is_green(repo_root: Path, tmp_path: Path) -> None:
    """The control every arm below leans on: no mutation, no failure."""
    test_no_absolute_checkout_path_in_any_tracked_text_file(_planted_tree(repo_root, tmp_path, {}))


def test_the_guard_file_is_scanned_like_any_other(repo_root: Path, tmp_path: Path) -> None:
    """F1, mutant ``self``: a root constant appended to the guard file's own foot fails."""
    relative = "tests/test_readme_audit.py"
    data = (repo_root / relative).read_bytes() + f'ROOT = "{_PLANTED}"\n'.encode()
    assert relative in _guard_failure(_planted_tree(repo_root, tmp_path, {relative: data}))


def test_a_second_spelling_on_a_kept_line_fails(repo_root: Path, tmp_path: Path) -> None:
    """F2, mutant ``kept_same_line``: the line count holds, the line's content does not."""
    lines, index = _kept_lines(repo_root, "CLAUDE.md")
    lines[index] += f" and `{_PLANTED}`"
    data = "\n".join(lines).encode()
    assert "CLAUDE.md" in _guard_failure(_planted_tree(repo_root, tmp_path, {"CLAUDE.md": data}))


def test_a_kept_spelling_moved_to_a_new_line_fails(repo_root: Path, tmp_path: Path) -> None:
    """F2, mutant ``kept_move``: one kept line scrubbed, one new spelling added elsewhere."""
    lines, index = _kept_lines(repo_root, "CLAUDE.md")
    lines[index] = ABSOLUTE_CHECKOUT_RE.sub("<repo>", lines[index])
    lines.insert(len(lines) - 1, f"See `{_PLANTED_WSL}`.")
    data = "\n".join(lines).encode()
    assert "CLAUDE.md" in _guard_failure(_planted_tree(repo_root, tmp_path, {"CLAUDE.md": data}))


def test_a_line_shift_above_a_kept_line_stays_green(repo_root: Path, tmp_path: Path) -> None:
    """F2's control: an edit and an insertion above a kept line move it, and that is green."""
    lines, index = _kept_lines(repo_root, "CLAUDE.md")
    assert index > 1, "the control needs a line above the first kept line"
    lines[0] += " (edited)"
    lines.insert(1, "A line inserted above every kept line.")
    data = "\n".join(lines).encode()
    test_no_absolute_checkout_path_in_any_tracked_text_file(
        _planted_tree(repo_root, tmp_path, {"CLAUDE.md": data})
    )


def test_a_nul_byte_does_not_hide_a_spelling(repo_root: Path, tmp_path: Path) -> None:
    """F3, mutant ``nul``: one NUL no longer makes a text file binary and skipped."""
    relative = "docs/ARCHITECTURE.md"
    data = f"# Architecture\n\0\nThe root is {_PLANTED}.\n".encode()
    assert relative in _guard_failure(_planted_tree(repo_root, tmp_path, {relative: data}))


@pytest.mark.parametrize("codec", ["utf-16", "utf-16-le", "utf-16-be", "utf-32-le"])
def test_a_wide_encoding_does_not_hide_a_spelling(
    repo_root: Path, tmp_path: Path, codec: str
) -> None:
    """F3, mutant ``utf16``: a wide re-encoding, with a byte-order mark or none, is read."""
    relative = "docs/GATED.md"
    data = f"# Gated\n\nThe root is {_PLANTED}.\n".encode(codec)
    assert relative in _guard_failure(_planted_tree(repo_root, tmp_path, {relative: data}))


def test_an_undecodable_file_fails_as_unscannable(repo_root: Path, tmp_path: Path) -> None:
    """F3: a file no decoding reads fails by name, never passes as clean."""
    relative = "docs/notes.txt"
    message = _guard_failure(_planted_tree(repo_root, tmp_path, {relative: b"caf\xe9 au lait\n"}))
    assert "unscannable" in message
    assert relative in message


def test_only_a_hash_pinned_binary_is_skipped(repo_root: Path, tmp_path: Path) -> None:
    """F3: a pinned image is skipped by path AND bytes, so changed bytes are scanned."""
    pins = "tools/sha_citation_binaries.json"
    image = "docs/assets/dashboard.png"
    real = {pins: (repo_root / pins).read_bytes(), image: (repo_root / image).read_bytes()}
    test_no_absolute_checkout_path_in_any_tracked_text_file(
        _planted_tree(repo_root, tmp_path / "clean", real)
    )
    smuggled = dict(real)
    smuggled[image] = real[image] + f"tEXt\0root={_PLANTED}\n".encode()
    assert image in _guard_failure(_planted_tree(repo_root, tmp_path / "smuggled", smuggled))


def test_an_unpinned_binary_is_scanned(repo_root: Path, tmp_path: Path) -> None:
    """F3: a NUL-bearing file outside the pins is read, not waved through as binary."""
    relative = "docs/assets/planted.png"
    data = b"\x89PNG\r\n\x1a\n\0\0\0\rIHDR" + f"tEXt\0root={_PLANTED}\n".encode()
    assert relative in _guard_failure(_planted_tree(repo_root, tmp_path, {relative: data}))


# --- CS-1308 fix round 2 ---------------------------------------------------------


def test_a_kept_line_removed_fails_as_missing(repo_root: Path, tmp_path: Path) -> None:
    """Mutant M6: a kept line scrubbed with nothing added elsewhere fails as missing."""
    lines, index = _kept_lines(repo_root, "CLAUDE.md")
    lines[index] = ABSOLUTE_CHECKOUT_RE.sub("<repo>", lines[index])
    data = "\n".join(lines).encode()
    message = _guard_failure(_planted_tree(repo_root, tmp_path, {"CLAUDE.md": data}))
    assert "CLAUDE.md: 0 unexpected, 1 missing" in message


def test_a_nul_inside_the_spelling_does_not_hide_it(repo_root: Path, tmp_path: Path) -> None:
    """R3: a NUL between the drive colon and the separator does not split the spelling."""
    relative = "docs/ARCHITECTURE.md"
    spelled = _PLANTED.replace(":", ":\0").encode()
    data = b"# Architecture\n\nThe root is " + spelled + b".\n"
    assert relative in _guard_failure(_planted_tree(repo_root, tmp_path, {relative: data}))


def test_interleaved_nuls_do_not_hide_a_spelling(repo_root: Path, tmp_path: Path) -> None:
    """R3: two NULs after every character match no wide code unit, and still are read."""
    relative = "docs/ARCHITECTURE.md"
    spelled = b"".join(char.encode() + b"\0\0" for char in _PLANTED)
    data = b"# Architecture\n\n" + spelled + b"\n"
    assert relative in _guard_failure(_planted_tree(repo_root, tmp_path, {relative: data}))


@pytest.mark.parametrize("before", ["", "\u4100"], ids=["plain", "letter-shadow"])
def test_a_wide_spelling_inside_utf8_text_does_not_hide(
    repo_root: Path, tmp_path: Path, before: str
) -> None:
    """R3: valid UTF-8 text, one U+0600, then a UTF-16-LE spelling.

    The U+0600's UTF-8 bytes sit where a strict UTF-16 read aligned on the spelling
    meets an unpaired surrogate, so no strict wide view holds it. In ``letter-shadow``
    a U+4100 stands before the spelling: its UTF-16-LE bytes are a NUL and an ``A``,
    so with every NUL removed a letter sits glued in front of the Git Bash form, and
    only a lenient wide read sees the spelling as written.
    """
    relative = "docs/GATED.md"
    git_bash = _PLANTED_WSL.removeprefix("/mnt")
    data = "# Gated\n\u0600\n".encode() + f"{before}{git_bash}\n".encode("utf-16-le")
    assert relative in _guard_failure(_planted_tree(repo_root, tmp_path, {relative: data}))


@pytest.mark.parametrize("resolving", [False, True], ids=["dangling", "resolving"])
def test_a_symlink_entry_is_scanned_by_its_link_text(
    repo_root: Path, tmp_path: Path, *, resolving: bool
) -> None:
    """R4: a symlink's index blob - the link text git publishes - is read, never followed.

    ``dangling`` has nothing in the work tree at the path; ``resolving`` has a clean file
    there, standing for the target a followed link would open. The link text's line is
    counted as one unexpected spelling, so a guard that failed the link as unscannable
    instead of reading it (mutant M1) fails this arm.
    """
    relative = "docs/link.md"
    files = {relative: b"# A clean target\n"} if resolving else {}
    entry = {relative: (_SYMLINK_MODE, _PLANTED.encode())}
    message = _guard_failure(_planted_tree(repo_root, tmp_path, files, entry))
    assert f"{relative}: 1 unexpected, 0 missing" in message
    assert "unscannable" not in message


def test_a_tracked_file_missing_from_the_work_tree_is_read_from_the_index(
    repo_root: Path, tmp_path: Path
) -> None:
    """R4: a tracked file absent from the work tree is read from its index blob, not skipped.

    The blob's line is counted as one unexpected spelling, so a guard that failed the
    path as unscannable instead of reading its blob (mutant M2) fails this arm.
    """
    relative = "docs/gone.md"
    entry = {relative: ("100644", f"The root is {_PLANTED}.\n".encode())}
    message = _guard_failure(_planted_tree(repo_root, tmp_path, {}, entry))
    assert f"{relative}: 1 unexpected, 0 missing" in message
    assert "unscannable" not in message


def test_an_unreadable_tracked_path_fails_as_unscannable(repo_root: Path, tmp_path: Path) -> None:
    """Mutant M17: a read error other than a missing file fails by path, never skips."""
    relative = "docs/folder.md"
    root = _planted_tree(repo_root, tmp_path, {}, {relative: ("100644", b"clean\n")})
    (root / relative).mkdir(parents=True)
    message = _guard_failure(root)
    assert "unscannable" in message
    assert relative in message


#: CS-1308 F5 - a quoted drive root and the quoted folder name on one line: the root
#: spelled in two parts, which the single-token pattern above cannot see.
TWO_PART_CHECKOUT_RE: Final = re.compile(
    r"""(?=.*["'][A-Za-z]:[\\/]*["'])(?=.*["']Clockspeed["'])""", re.IGNORECASE
)


def test_no_tracked_markdown_spells_the_root_in_two_quoted_parts(repo_root: Path) -> None:
    """F5. In prose a quoted drive root beside the quoted folder name is the root spelled.

    Markdown only: in code, a spelling assembled from fragments is the recorded residual
    of the CS-1308 decision record in ``docs/LEDGER.md``, which no line pattern closes.
    It reads each file through the whole-tree guard's views, which fails a file none of
    them decodes. The message names paths and counts only.
    """
    found: dict[str, int] = {}
    for relative in doc_sweep.tracked_files(repo_root):
        path = repo_root / relative
        if relative.endswith(".md") and path.is_file():
            views = _decodings(path.read_bytes()) or []
            lines = [line for view in views for line in view.splitlines()]
            count = sum(1 for line in lines if TWO_PART_CHECKOUT_RE.match(line))
            if count:
                found[relative] = count
    assert not found, f"markdown spells the root in two quoted parts (path: lines): {found}"
