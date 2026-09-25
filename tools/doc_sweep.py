#!/usr/bin/env python3
"""CS-1184 - the orphan, staleness and anchor sweep over tracked markdown.

WHAT THIS OWNS, AND WHAT IT DOES NOT. Relative-link RESOLUTION already runs on
every push, in the ``Markdown link check`` step of ``.github/workflows/tier1.yml``:
it strips fragments, never fetches a URL, and runs no orphan or staleness sweep.
This tool is the remainder of gate item 6 and does not repeat that step - a
fragment whose TARGET FILE is missing is skipped and counted here, because
reporting it is the tier-1 step's job.

THE CLI CONTRACT, published for CS-1183's tier-3 job, which codes against it:

    python tools/doc_sweep.py [--urls] [--root DIR]

    exit 0   clean - nothing found
    exit 1   findings - one line per finding on stdout
    exit 2   could not run - no git, not the top of a work tree, or no tracked
             markdown at all; the reason goes to stderr

    stdout always carries ``skipped: N`` before the findings, with N broken down
    by reason, so a run that checked nothing cannot read as a clean one.

    ``--urls`` is the ONLY path that touches the network, and it is what the
    tier-3 job calls. Without it every external URL is skipped and counted, so
    the push lanes stay deterministic and offline. ``--root`` defaults to the
    repository this file lives in; the arms point it at throwaway repositories.

THE POPULATION is ``git ls-files`` - TRACKED files only, resolved through
``tools/toolpath.py``. An untracked file is invisible to this sweep by design, and
an empty markdown population is refused (exit 2) rather than reported clean,
because an empty population satisfies every zero.

RULE 1 - ORPHAN AND UNREACHABLE. A tracked ``.md`` file is LIVE when it is a root
(:data:`ROOTS`), is named by :data:`ALLOWLIST`, is referenced by a tracked file
that is not markdown, or is referenced by a live markdown file. A REFERENCE is
any path token ending in ``.md`` - a link target, a code span, bare prose, code
or configuration - that resolves to a tracked markdown file either relative to
the referring file's directory or relative to the repository root. The rule is
generous on purpose: this repository cites files in code spans far more often
than in links, and a file named that way has still been routed to. A file never
references itself, and :data:`REFERRER_EXCLUDED` names the files whose mentions
are not references at all.

A MENTION NOBODY CAN FOLLOW IS NOT A REFERENCE. Inside a markdown file, a path
in a fenced code block or in an HTML comment does not count: the fence renders
as literal text and the comment does not render at all. Code SPANS still count,
for the reason above. What is NOT excluded, stated rather than implied: an
INDENTED code block. Telling one from a list item's indented continuation takes
a full CommonMark parse, and the error that remains can only hide an orphan,
never invent one. YAML front matter still counts too - GitHub renders it as a
visible table. Mentions in tracked files that are not markdown always count.

``docs/_archive/`` IS EXCUSED FROM THIS RULE. ``CLAUDE.md`` section 4 sends dated
artifacts there, deliberately excluded from search so they never pollute a
search for current truth - an archived file is SUPPOSED to be referenced by
nothing live. It is never reported as ORPHAN or UNREACHABLE, and it is NOT a
root either: a file referenced only from the archive is still reported. Rules
2, 3 and 5 grade archived files like any other.

A markdown file that is not live, and not archived, is reported as

  * ``ORPHAN`` when no other tracked file references it - the acceptance's own
    set, exactly - or
  * ``UNREACHABLE`` when it IS referenced, but only by markdown that is itself
    not live: an island, or a leaf hanging off an orphan.

RULE 2 - DEAD ANCHOR. Every fragment in a markdown link target - inline, image
or reference definition, outside fenced code, code spans, HTML comments and YAML
front matter - is checked
against the anchors of its target when that target is a tracked markdown file.
The anchors are the heading fragments GitHub generates (:class:`Slugger`) plus
every HTML ``id`` or ``name`` attribute. Comparison is exact after
percent-decoding. A fragment into a non-markdown target, into a target that is
not tracked, or an empty fragment is skipped and counted.

GITHUB'S HEADING RULE, as implemented by :class:`Slugger`: render the heading's
inline markup to text (code spans keep their content, links and images keep
their text, an autolink keeps its address, HTML tags go, PAIRED underscore
emphasis delimiters go and an unpaired underscore stays), lowercase it, drop
every character that is not a letter, digit, mark, connector punctuation, space
or hyphen, then turn EACH space into one hyphen - so ``a - b`` is ``a---b``. A
multi-line setext heading's line break is dropped by the same character rule. A
slug already issued in the same file gets ``-1``, ``-2`` and so on, re-checked
against every slug issued so far. The emphasis step approximates CommonMark's
flanking rules: a run of one to three underscores is a delimiter only where a
matching run closes it and no letter, digit or underscore stands outside either.

WHICH HEADINGS GET AN ANCHOR. GitHub anchors every rendered heading element, so
an ATX heading counts inside a blockquote or a list item as well as at top
level, and so does a setext heading whose underline sits at the same blockquote
depth as its text. A line of dashes under a list item, or under a quote it
cannot continue, is a thematic break and anchors nothing. Nothing inside a
fence, an HTML comment or YAML front matter is a heading - none of them render
as one.

RULE 3 - STALE. ``CLAUDE.md`` section 4 sends dated artifacts to
``docs/_archive/``. A tracked markdown file outside that directory is STALE when
its file name carries an ISO date, or when it declares itself
``**Section status: HISTORICAL`` at the start of a line - unless
:data:`STALE_ALLOWLIST` names it. That allowlist holds the two append-only
records whose owner rows in the topology table put them outside the archive.

RULE 4 - STALE ALLOWLIST. An entry in :data:`ALLOWLIST` or
:data:`STALE_ALLOWLIST` that matches no tracked markdown file is itself a
finding, so an excuse cannot outlive the file it excused.

RULE 5 - DEAD URL, ``--urls`` only. Every distinct ``http`` or ``https`` URL in a
markdown link, an autolink or bare prose, outside fenced code, code spans, HTML
comments and YAML front matter, is
fetched once; a status of 400 or above, or any error, is a finding. A URL whose
host is on :data:`NO_FETCH_HOSTS` is never fetched and is counted as skipped.

EVERY MESSAGE names repo-relative paths only - never the absolute root, never
file bytes beyond the offending link target.
"""

from __future__ import annotations

import argparse
import html
import os
import posixpath
import re
import subprocess
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

# `tools` carries no __init__.py, so the sibling resolver is imported under its
# BARE name, the way tools/provenance_stamp.py does it.
_TOOLS_DIR: Final = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402

REPO_ROOT: Final = _TOOLS_DIR.parent

EXIT_CLEAN: Final = 0
EXIT_FINDINGS: Final = 1
EXIT_COULD_NOT_RUN: Final = 2

GIT_TIMEOUT_SECONDS: Final = 60
URL_TIMEOUT_SECONDS: Final = 20

#: The first status that counts as a dead URL.
HTTP_ERROR_FLOOR: Final = 400

#: Statuses a server answers HEAD with while GET would succeed; retried as GET.
HEAD_REFUSED: Final = frozenset({403, 405})

MARKDOWN_SUFFIX: Final = ".md"
ARCHIVE_PREFIX: Final = "docs/_archive/"

# --- finding kinds and skip reasons ----------------------------------------

ORPHAN: Final = "ORPHAN"
UNREACHABLE: Final = "UNREACHABLE"
DEAD_ANCHOR: Final = "DEAD-ANCHOR"
STALE: Final = "STALE"
STALE_EXCUSE: Final = "STALE-ALLOWLIST"
DEAD_URL: Final = "DEAD-URL"

SKIP_EXTERNAL_URL: Final = "external-url-without---urls"
SKIP_NO_FETCH_HOST: Final = "no-fetch-host"
SKIP_NON_HTTP_SCHEME: Final = "non-http-link"
SKIP_NON_MARKDOWN_TARGET: Final = "fragment-into-non-markdown"
SKIP_UNTRACKED_TARGET: Final = "fragment-into-untracked-target"
SKIP_EMPTY_FRAGMENT: Final = "empty-fragment"
SKIP_UNREADABLE: Final = "unreadable-or-binary-file"

# --- the named tables, every entry with its reason --------------------------

#: The reachability roots. Never reported, whether referenced or not.
ROOTS: Final[Mapping[str, str]] = {
    "README.md": "the outsider entry point GitHub renders at the repository root",
    "CLAUDE.md": "auto-loaded by the harness every turn; it owns the doc topology",
}

#: Files and directory prefixes (ending in ``/``) that are live without a
#: reference, because something other than a link loads them.
ALLOWLIST: Final[Mapping[str, str]] = {
    ".claude/agents/": "the harness loads every agent definition in this directory by name",
    ".claude/commands/": "the harness loads every slash command in this directory by name",
    ".github/CODE_OF_CONDUCT.md": "GitHub surfaces it on the community profile by convention",
    ".github/CONTRIBUTING.md": "GitHub links it from the issue and pull request pages",
    ".github/PULL_REQUEST_TEMPLATE.md": "GitHub pre-fills every new pull request with it",
    ".github/SECURITY.md": "GitHub surfaces it as the repository security policy",
}

#: Records that declare themselves HISTORICAL but whose owner row in the
#: ``CLAUDE.md`` topology table places them outside ``docs/_archive/``.
STALE_ALLOWLIST: Final[Mapping[str, str]] = {
    "docs/LEDGER.md": "the append-only completion record; the topology table owns its path",
    "docs/history_notes.md": "the deep archive of pruned notes; the topology table owns its path",
}

#: Tracked files whose mentions of a markdown path are not references.
REFERRER_EXCLUDED: Final[Mapping[str, str]] = {
    "tools/provenance.tsv": "a manifest lists every tracked path by construction - a census row",
    "tools/doc_sweep.py": "the sweep's own tables and prose name the files they excuse",
    "tests/test_doc_sweep.py": "the sweep's arms cite headings by file as provenance only",
}

#: Hosts ``--urls`` never fetches, matched on the host or any subdomain of it.
NO_FETCH_HOSTS: Final[Mapping[str, str]] = {
    "wiki.gg": (
        "the official wiki's platform; docs/upstream_watch.md and the CS-485 ledger "
        "entry forbid any automated fetch of it, a one-off check included"
    ),
}

# --- markdown shapes -------------------------------------------------------

#: A path token ending in ``.md``: never preceded by a path character, so the
#: tail of a URL is not read as a repository path.
_MD_PATH: Final = re.compile(
    r"(?<![A-Za-z0-9_.\-/\\])((?:[A-Za-z0-9_.\-]+/)*[A-Za-z0-9_.\-]+\.md)(?![A-Za-z0-9_\-])"
)
_FENCE: Final = re.compile(r"^(?P<indent> *)(?P<run>`{3,}|~{3,})(?P<info>.*)$")
_MAX_FENCE_INDENT: Final = 3
_CODE_SPAN: Final = re.compile(r"(`+)(.+?)\1")
#: Anchored on the ``](`` join rather than the whole ``[text](target)`` so a
#: badge - an image nested inside a link - yields both of its targets.
_INLINE_LINK: Final = re.compile(r"\]\(\s*<?([^)>\s]+)>?(?:\s+[\"'(][^)]*)?\s*\)")
_REF_DEF: Final = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*<?([^\s>]+)>?")
_AUTOLINK: Final = re.compile(r"<(https?://[^>\s]+)>", re.IGNORECASE)
_BARE_URL: Final = re.compile(r"(?<![<(\[\w/])https?://[^\s<>()\[\]`'\"]+", re.IGNORECASE)
_URL_TRAILING: Final = ".,;:!?*_"
_SCHEME: Final = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")
_ATX: Final = re.compile(r"^ {0,3}#{1,6}(?:[ \t]+(.*?))?[ \t]*$")
_ATX_CLOSING: Final = re.compile(r"(?:^|[ \t]+)#+$")
_SETEXT: Final = re.compile(r"^ {0,3}(?:=+|-+)[ \t]*$")
_HTML_ID: Final = re.compile(r"<[A-Za-z][^>]*?\s(?:id|name)\s*=\s*[\"']([^\"']+)[\"']")
_HTML_TAG: Final = re.compile(r"<[^>]+>")
_IMAGE: Final = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_LINK: Final = re.compile(r"\[([^\]]*)\](?:\([^)]*\)|\[[^\]]*\])")
_ESCAPE: Final = re.compile(r"\\([!-/:-@\[-`{-~])")
_EMPHASIS_UNDERSCORE: Final = re.compile(
    r"(?<![A-Za-z0-9_])(_{1,3})(?=[^\s_])(.+?)(?<=[^\s_])\1(?![A-Za-z0-9_])"
)
_AUTOLINK_ANY: Final = re.compile(r"<([A-Za-z][A-Za-z0-9+.\-]{1,31}:[^<>\s]*|[^<>\s@]+@[^<>\s@]+)>")
_QUOTE_MARKER: Final = re.compile(r"^ {0,3}> ?")
_LIST_MARKER: Final = re.compile(r"^ {0,3}(?:[-+*]|\d{1,9}[.)])(?:[ \t]+|$)")
_THEMATIC_BREAK: Final = re.compile(r"^ {0,3}(?:(?:-[ \t]*){3,}|(?:\*[ \t]*){3,}|(?:_[ \t]*){3,})$")
_COMMENT_OPEN: Final = "<!--"
_COMMENT_CLOSE: Final = "-->"
_FRONT_MATTER_OPEN: Final = "---"
_FRONT_MATTER_CLOSE: Final = ("---", "...")
_DATED_NAME: Final = re.compile(r"\d{4}-\d{2}-\d{2}")
_HISTORICAL: Final = re.compile(r"^\*\*Section status:[ \t]*HISTORICAL\b", re.MULTILINE)

#: Escaped punctuation is parked in the Private Use Area while emphasis and
#: link markup are stripped, then restored, so ``\_`` survives as ``_``.
_PARK_BASE: Final = 0xE000


class CouldNotRunError(Exception):
    """The sweep could not measure anything; the CLI exits 2."""


@dataclass(frozen=True)
class Finding:
    """One reportable fault: its kind, the repo-relative file, and a detail."""

    kind: str
    path: str
    detail: str


@dataclass
class Report:
    """What one sweep measured and found."""

    markdown_files: int = 0
    referrer_files: int = 0
    fragments_checked: int = 0
    urls_checked: int = 0
    skips: dict[str, int] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)

    @property
    def skipped(self) -> int:
        """The total of every skip reason."""
        return sum(self.skips.values())

    def skip(self, reason: str, count: int = 1) -> None:
        """Count ``count`` skips under ``reason``."""
        self.skips[reason] = self.skips.get(reason, 0) + count


# --- GitHub's heading-to-fragment rule ---------------------------------------


def _render_inline(text: str) -> str:
    """Render one heading's inline markup to the text GitHub slugs.

    Args:
        text: The raw heading text, markers already removed.

    Returns:
        The text a reader sees: code spans keep their content, links and
        images their text, and HTML tags and emphasis delimiters are dropped.
    """
    rendered: list[str] = []
    cursor = 0
    for span in _CODE_SPAN.finditer(text):
        rendered.append(_render_plain(text[cursor : span.start()]))
        rendered.append(span.group(2))
        cursor = span.end()
    rendered.append(_render_plain(text[cursor:]))
    return "".join(rendered)


def _render_plain(text: str) -> str:
    """Render markup outside code spans; see :func:`_render_inline`."""
    parked = _ESCAPE.sub(lambda m: chr(_PARK_BASE + ord(m.group(1))), text)
    parked = _IMAGE.sub(r"\1", parked)
    parked = _LINK.sub(r"\1", parked)
    parked = _AUTOLINK_ANY.sub(r"\1", parked)
    parked = _HTML_TAG.sub("", parked)
    unpaired = ""
    while unpaired != parked:
        unpaired, parked = parked, _EMPHASIS_UNDERSCORE.sub(r"\2", parked)
    parked = html.unescape(parked)
    return "".join(
        chr(ord(ch) - _PARK_BASE) if _PARK_BASE <= ord(ch) < _PARK_BASE + 0x80 else ch
        for ch in parked
    )


def slugify(text: str) -> str:
    """Apply GitHub's character rule to already-rendered heading text.

    Args:
        text: Rendered heading text.

    Returns:
        The fragment before any duplicate suffix.
    """
    kept: list[str] = []
    for ch in text.strip().lower():
        if ch == " ":
            kept.append("-")
        elif ch in "-_" or (ch.isascii() and ch.isalnum()):
            kept.append(ch)
        elif not ch.isascii():
            category = unicodedata.category(ch)
            if category[0] in "LMN" or category == "Pc":
                kept.append(ch)
    return "".join(kept)


class Slugger:
    """GitHub's slugger for ONE file: each heading in order, duplicates suffixed."""

    def __init__(self) -> None:
        """Start with no slug issued."""
        self._occurrences: dict[str, int] = {}

    def slug(self, heading: str) -> str:
        """Return the fragment GitHub gives ``heading`` at this point in the file.

        Args:
            heading: The raw heading text, with its markup.

        Returns:
            The fragment, suffixed ``-N`` past every slug already issued.
        """
        base = slugify(_render_inline(heading))
        candidate = base
        while candidate in self._occurrences:
            self._occurrences[base] += 1
            candidate = f"{base}-{self._occurrences[base]}"
        self._occurrences[candidate] = 0
        return candidate


def _front_matter_end(lines: Sequence[str]) -> int:
    """Return how many leading lines are YAML front matter, or 0 when there is none."""
    if not lines or lines[0].rstrip() != _FRONT_MATTER_OPEN:
        return 0
    for index in range(1, len(lines)):
        if lines[index].rstrip() in _FRONT_MATTER_CLOSE:
            return index + 1
    return 0


def _blank_comments(line: str, *, open_comment: bool) -> tuple[str, bool]:
    """Remove HTML comment text from one line.

    An opener inside a code span is literal and opens nothing.

    Args:
        line: One source line.
        open_comment: Whether a comment opened on an earlier line is still open.

    Returns:
        The visible remainder, and whether a comment is still open at its end.
    """
    spans = [(m.start(), m.end()) for m in _CODE_SPAN.finditer(line)]
    visible: list[str] = []
    cursor = 0
    if open_comment:
        end = line.find(_COMMENT_CLOSE)
        if end < 0:
            return "", True
        cursor = end + len(_COMMENT_CLOSE)
    while True:
        start = line.find(_COMMENT_OPEN, cursor)
        while start >= 0 and any(a <= start < b for a, b in spans):
            start = line.find(_COMMENT_OPEN, start + 1)
        if start < 0:
            visible.append(line[cursor:])
            return "".join(visible), False
        visible.append(line[cursor:start])
        # From the opener's third character, so the empty comments "<!-->" and
        # "<!--->" close where CommonMark closes them.
        end = line.find(_COMMENT_CLOSE, start + 2)
        if end < 0:
            return "".join(visible), True
        cursor = end + len(_COMMENT_CLOSE)


def _visible_lines(text: str, *, front_matter: bool) -> Iterator[tuple[int, str]]:
    """Yield ``(line_number, line)`` for every line a reader can see rendered.

    Fenced code lines are not yielded at all. HTML comment text is blanked out
    of the lines it touches. A fence opens on a run of three or more backticks
    or tildes indented at most three spaces, and closes on a run of the same
    character at least as long, carrying nothing else.

    Args:
        text: The markdown source.
        front_matter: Whether YAML front matter lines are yielded too.
    """
    lines = text.splitlines()
    first = 0 if front_matter else _front_matter_end(lines)
    fence: str | None = None
    in_comment = False
    for number, raw in enumerate(lines[first:], first + 1):
        line = raw
        if not in_comment and fence is not None:
            match = _FENCE.match(line)
            run = match.group("run") if match else ""
            closes = bool(match) and run[0] == fence[0] and len(run) >= len(fence)
            if closes and match and not match.group("info").strip():
                fence = None
            continue
        if not in_comment:
            match = _FENCE.match(line)
            if match and len(match.group("indent")) <= _MAX_FENCE_INDENT:
                fence = match.group("run")
                continue
        line, in_comment = _blank_comments(line, open_comment=in_comment)
        yield number, line


def _containers(line: str) -> tuple[int, str, str, bool]:
    """Strip blockquote and list-item markers from the front of one line.

    Returns:
        The blockquote depth, the line after the quote markers, the line after
        every marker, and whether a list-item marker was among them.
    """
    depth = 0
    rest = line
    while quote := _QUOTE_MARKER.match(rest):
        depth += 1
        rest = rest[quote.end() :]
    inner = rest
    list_item = False
    while True:
        if quote := _QUOTE_MARKER.match(rest):
            rest = rest[quote.end() :]
        elif item := _LIST_MARKER.match(rest):
            list_item = True
            rest = rest[item.end() :]
        else:
            return depth, inner, rest, list_item


def anchors(text: str) -> set[str]:
    """Every fragment a link into this markdown can land on.

    Args:
        text: The markdown source.

    Returns:
        The heading slugs, in GitHub's rule, plus every HTML ``id``/``name``.
    """
    slugger = Slugger()
    found: set[str] = set()
    paragraph: list[str] = []
    eligible = False
    paragraph_depth = 0
    last_number = 0
    for number, line in _visible_lines(text, front_matter=False):
        if number != last_number + 1:
            paragraph = []
        last_number = number
        found.update(_HTML_ID.findall(line))
        depth, inner, body, list_item = _containers(line)
        atx = _ATX.match(body)
        if atx:
            heading = _ATX_CLOSING.sub("", (atx.group(1) or "").strip())
            found.add(slugger.slug(heading))
            paragraph = []
            continue
        if paragraph and eligible and depth == paragraph_depth and _SETEXT.match(inner):
            found.add(slugger.slug("\n".join(paragraph)))
            paragraph = []
            continue
        if not body.strip() or _THEMATIC_BREAK.match(inner):
            paragraph = []
            continue
        if not paragraph or depth != paragraph_depth or list_item:
            if not paragraph and not list_item and body.startswith(("    ", "\t")):
                continue
            paragraph = []
            # A paragraph opened by a list item is never a setext heading's
            # text: dashes under it are a thematic break.
            eligible = not list_item
            paragraph_depth = depth
        paragraph.append(body.strip())
    return found


# --- git ---------------------------------------------------------------------


def _child_env() -> dict[str, str]:
    """Return the environment minus every ``GIT_`` variable.

    A pre-push hook exports ``GIT_DIR``; inheriting it would list a different
    repository from the one ``--root`` names.
    """
    return {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}


def _git(root: Path, *args: str) -> str:
    """Run git against ``root`` and return stdout.

    Raises:
        CouldNotRunError: git is absent or the command failed.
    """
    git = resolve_tool("git")
    if git is None:
        message = "git is not on PATH; the tracked population cannot be read"
        raise CouldNotRunError(message)
    try:
        completed = subprocess.run(
            [git, "-C", str(root), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
            env=_child_env(),
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        message = f"git {args[0]} did not complete ({type(error).__name__})"
        raise CouldNotRunError(message) from error
    if completed.returncode != 0:
        message = f"git {args[0]} failed with exit {completed.returncode}; is --root a work tree?"
        raise CouldNotRunError(message)
    return completed.stdout


def tracked_files(root: Path) -> list[str]:
    """Return every tracked path under ``root``, which must be a work-tree top.

    Raises:
        CouldNotRunError: not a repository, or not its top level.
    """
    if not root.is_dir():
        message = "--root is not a directory"
        raise CouldNotRunError(message)
    if _git(root, "rev-parse", "--show-prefix").strip():
        message = "--root is inside a work tree but is not its top level"
        raise CouldNotRunError(message)
    return sorted({name for name in _git(root, "ls-files", "-z").split("\0") if name})


# --- the sweep ---------------------------------------------------------------


def _read_text(root: Path, name: str) -> str | None:
    """Return a tracked file's text, or None when it is absent or binary."""
    try:
        data = (root / name).read_bytes()
    except OSError:
        return None
    if b"\0" in data:
        return None
    return data.decode("utf-8", errors="replace")


def _resolve(referrer: str, token: str, markdown: set[str]) -> str | None:
    """Resolve a path token from ``referrer`` to a tracked markdown file.

    Tried relative to the referrer's directory first, then to the root.
    """
    for base in (posixpath.dirname(referrer), ""):
        candidate = posixpath.normpath(posixpath.join(base, token.lstrip("/")))
        if candidate in markdown:
            return candidate
    return None


def _references(referrer: str, text: str, markdown: set[str]) -> set[str]:
    """Every tracked markdown file ``text`` names, itself excluded.

    In markdown, only what renders visibly counts - see rule 1.
    """
    if referrer.endswith(MARKDOWN_SUFFIX):
        text = "\n".join(line for _, line in _visible_lines(text, front_matter=True))
    found = {_resolve(referrer, token, markdown) for token in _MD_PATH.findall(text)}
    return {name for name in found if name is not None and name != referrer}


def _allowlisted(name: str, table: Mapping[str, str]) -> bool:
    """Whether ``name`` is an entry of ``table`` or under a ``/`` prefix entry."""
    return any(name.startswith(entry) if entry.endswith("/") else name == entry for entry in table)


def _stale_entries(table: Mapping[str, str], markdown: set[str]) -> list[str]:
    """The entries of ``table`` that match no tracked markdown file."""
    return [entry for entry in table if not any(_allowlisted(n, {entry: ""}) for n in markdown)]


def _link_targets(text: str) -> Iterator[tuple[int, str]]:
    """Yield ``(line, target)`` for every link target outside code."""
    for number, line in _visible_lines(text, front_matter=False):
        bare = _CODE_SPAN.sub("", line)
        for target in _INLINE_LINK.findall(bare):
            yield number, target.strip()
        ref = _REF_DEF.match(bare)
        if ref:
            yield number, ref.group(1).strip()


def _urls(text: str) -> Iterator[tuple[int, str]]:
    """Yield ``(line, url)`` for every http(s) URL outside code."""
    for number, target in _link_targets(text):
        if target.lower().startswith(("http://", "https://")):
            yield number, target
    for number, line in _visible_lines(text, front_matter=False):
        bare = _CODE_SPAN.sub("", line)
        for url in _AUTOLINK.findall(bare):
            yield number, url
        for url in _BARE_URL.findall(bare):
            yield number, url.rstrip(_URL_TRAILING)


def _no_fetch(url: str, hosts: Mapping[str, str]) -> bool:
    """Whether ``url``'s host is a no-fetch host or a subdomain of one."""
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    return any(host == entry or host.endswith("." + entry) for entry in hosts)


def fetch_status(url: str) -> int:
    """Fetch ``url`` once and return its HTTP status. The ONLY network call.

    HEAD first; a server that refuses HEAD is asked again with GET.

    Raises:
        OSError: the URL could not be reached at all.
    """
    for method in ("HEAD", "GET"):
        request = urllib.request.Request(  # noqa: S310 - the caller passes http(s) only
            url, method=method, headers={"User-Agent": "clockspeed-doc-sweep"}
        )
        try:
            with urllib.request.urlopen(  # noqa: S310 - the caller passes http(s) only
                request, timeout=URL_TIMEOUT_SECONDS
            ) as response:
                return int(response.status)
        except urllib.error.HTTPError as error:
            if method == "HEAD" and error.code in HEAD_REFUSED:
                continue
            return int(error.code)
    return HTTP_ERROR_FLOOR


def _sweep_reachability(
    report: Report,
    texts: Mapping[str, str],
    markdown: set[str],
    allowlist: Mapping[str, str],
) -> None:
    """Rule 1: report every markdown file no live file reaches."""
    edges = {
        name: _references(name, text, markdown)
        for name, text in texts.items()
        if name not in REFERRER_EXCLUDED
    }
    inbound: dict[str, set[str]] = {name: set() for name in markdown}
    for referrer, targets in edges.items():
        for target in targets:
            inbound[target].add(referrer)
    live = {n for n in markdown if n in ROOTS or _allowlisted(n, allowlist)}
    for referrer, targets in edges.items():
        if not referrer.endswith(MARKDOWN_SUFFIX):
            live |= targets
    queue = deque(sorted(live))
    while queue:
        for target in sorted(edges.get(queue.popleft(), set()) - live):
            live.add(target)
            queue.append(target)
    for name in sorted(markdown - live):
        if name.startswith(ARCHIVE_PREFIX):
            continue
        if inbound[name]:
            detail = "referenced only by markdown no root reaches"
            report.findings.append(Finding(UNREACHABLE, name, detail))
        else:
            detail = "no other tracked file references it"
            report.findings.append(Finding(ORPHAN, name, detail))


def _sweep_anchors(report: Report, texts: Mapping[str, str], markdown: set[str]) -> None:
    """Rule 2: report every link fragment that matches no anchor in its target."""
    cache: dict[str, set[str]] = {}
    for source in sorted(markdown):
        text = texts.get(source)
        if text is None:
            continue
        for number, target in _link_targets(text):
            if "#" not in target or _SCHEME.match(target) or target.startswith("//"):
                continue
            path_part, fragment = target.split("#", 1)
            fragment = urllib.parse.unquote(fragment)
            if not fragment:
                report.skip(SKIP_EMPTY_FRAGMENT)
                continue
            path_part = urllib.parse.unquote(path_part)
            if not path_part:
                resolved: str | None = source
            else:
                base = "" if path_part.startswith("/") else posixpath.dirname(source)
                resolved = posixpath.normpath(posixpath.join(base, path_part.lstrip("/")))
            if resolved not in texts:
                report.skip(SKIP_UNTRACKED_TARGET)
                continue
            if resolved not in markdown:
                report.skip(SKIP_NON_MARKDOWN_TARGET)
                continue
            if resolved not in cache:
                cache[resolved] = anchors(texts[resolved])
            report.fragments_checked += 1
            if fragment not in cache[resolved]:
                detail = f"line {number}: {target} matches no heading in {resolved}"
                report.findings.append(Finding(DEAD_ANCHOR, source, detail))


def _sweep_staleness(
    report: Report,
    texts: Mapping[str, str],
    markdown: set[str],
    stale_allowlist: Mapping[str, str],
) -> None:
    """Rule 3: report dated or HISTORICAL markdown outside the archive."""
    for name in sorted(markdown):
        if name.startswith(ARCHIVE_PREFIX) or _allowlisted(name, stale_allowlist):
            continue
        if _DATED_NAME.search(posixpath.basename(name)):
            detail = f"a dated artifact outside {ARCHIVE_PREFIX}"
            report.findings.append(Finding(STALE, name, detail))
        elif _HISTORICAL.search(texts.get(name, "")):
            detail = f"declares itself HISTORICAL outside {ARCHIVE_PREFIX}"
            report.findings.append(Finding(STALE, name, detail))


def _sweep_urls(
    report: Report,
    texts: Mapping[str, str],
    markdown: set[str],
    *,
    check_urls: bool,
    fetch: Callable[[str], int],
) -> None:
    """Rule 5: fetch each distinct URL once, only when ``check_urls`` is set."""
    first_seen: dict[str, tuple[str, int]] = {}
    for source in sorted(markdown):
        for number, url in _urls(texts.get(source, "")):
            first_seen.setdefault(url, (source, number))
    for url, (source, number) in first_seen.items():
        if not check_urls:
            report.skip(SKIP_EXTERNAL_URL)
            continue
        if _no_fetch(url, NO_FETCH_HOSTS):
            report.skip(SKIP_NO_FETCH_HOST)
            continue
        report.urls_checked += 1
        try:
            status = fetch(url)
        # Any failure is a dead URL: urllib raises OSError and ValueError, and
        # http.client raises HTTPException, whose base class is neither.
        except Exception as error:
            detail = f"line {number}: {url} ({type(error).__name__})"
            report.findings.append(Finding(DEAD_URL, source, detail))
            continue
        if status >= HTTP_ERROR_FLOOR:
            detail = f"line {number}: {url} (HTTP {status})"
            report.findings.append(Finding(DEAD_URL, source, detail))


def sweep(
    root: Path,
    *,
    allowlist: Mapping[str, str] | None = None,
    stale_allowlist: Mapping[str, str] | None = None,
    check_urls: bool = False,
    fetch: Callable[[str], int] | None = None,
) -> Report:
    """Run every rule over the tracked markdown under ``root``.

    Args:
        root: The top of a git work tree.
        allowlist: Rule 1's allowlist; :data:`ALLOWLIST` when None.
        stale_allowlist: Rule 3's allowlist; :data:`STALE_ALLOWLIST` when None.
        check_urls: Whether rule 5 fetches; the ONLY network switch.
        fetch: The fetcher rule 5 uses; :func:`fetch_status` when None.

    Returns:
        The report, findings sorted by file then kind.

    Raises:
        CouldNotRunError: the population could not be read, or is empty.
    """
    live_table = ALLOWLIST if allowlist is None else allowlist
    stale_table = STALE_ALLOWLIST if stale_allowlist is None else stale_allowlist
    tracked = tracked_files(root)
    markdown = {name for name in tracked if name.endswith(MARKDOWN_SUFFIX)}
    if not markdown:
        message = "no tracked markdown; refusing to report a pass over an empty population"
        raise CouldNotRunError(message)
    report = Report(markdown_files=len(markdown))
    texts: dict[str, str] = {}
    for name in tracked:
        text = _read_text(root, name)
        if text is None:
            report.skip(SKIP_UNREADABLE)
        else:
            texts[name] = text
    report.referrer_files = len(texts)
    _sweep_reachability(report, texts, markdown, live_table)
    _sweep_anchors(report, texts, markdown)
    _sweep_staleness(report, texts, markdown, stale_table)
    for table in (live_table, stale_table):
        for entry in _stale_entries(table, markdown):
            detail = "an allowlist entry that matches no tracked markdown"
            report.findings.append(Finding(STALE_EXCUSE, entry, detail))
    _sweep_urls(report, texts, markdown, check_urls=check_urls, fetch=fetch or fetch_status)
    report.findings.sort(key=lambda f: (f.path, f.kind, f.detail))
    return report


# --- CLI -------------------------------------------------------------------


def _print_report(report: Report) -> None:
    """Print the counts, the skip breakdown, then one line per finding."""
    print(f"doc_sweep: markdown files scanned: {report.markdown_files}")
    print(f"doc_sweep: tracked files read as referrers: {report.referrer_files}")
    print(f"doc_sweep: fragments checked: {report.fragments_checked}")
    print(f"doc_sweep: urls checked: {report.urls_checked}")
    breakdown = ", ".join(f"{reason} {count}" for reason, count in sorted(report.skips.items()))
    print(f"doc_sweep: skipped: {report.skipped}" + (f" ({breakdown})" if breakdown else ""))
    for finding in report.findings:
        print(f"{finding.kind} {finding.path}: {finding.detail}")
    print(f"doc_sweep: findings: {len(report.findings)}")


def main(
    argv: Sequence[str] | None = None,
    *,
    fetch: Callable[[str], int] | None = None,
) -> int:
    """Run the sweep and return the published exit code.

    Args:
        argv: Arguments, without the program name; ``sys.argv`` when None.
        fetch: The ``--urls`` fetcher; :func:`fetch_status` when None.

    Returns:
        0 clean, 1 findings, 2 could not run.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument(
        "--urls",
        action="store_true",
        help="also fetch every external URL - the tier-3 job only, never on push",
    )
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="the work tree to sweep")
    args = parser.parse_args(argv)
    try:
        report = sweep(args.root, check_urls=args.urls, fetch=fetch)
    except CouldNotRunError as error:
        print(f"doc_sweep: could not run: {error}", file=sys.stderr)
        return EXIT_COULD_NOT_RUN
    _print_report(report)
    return EXIT_FINDINGS if report.findings else EXIT_CLEAN


if __name__ == "__main__":
    sys.exit(main())
