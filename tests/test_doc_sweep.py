"""CS-1184 - the orphan, staleness and anchor sweep over tracked markdown.

Every arm that grades a FINDING builds a throwaway git repository and COMMITS its
plant, because the sweep's population is what git tracks: an untracked plant is
invisible to an ls-files population, so an arm that only wrote the file would pass
for that reason and prove nothing (the arm
``test_an_untracked_plant_is_outside_the_population`` states that boundary out
loud rather than leaving it implied).

Every clean arm also asserts the sweep SAW a population. An empty population
satisfies every zero, so "no findings" is only evidence beside a non-trivial file
count.

No arm touches the network. The ``--urls`` arms hand the sweep a stub fetcher,
and the default-path arm replaces the standard library's opener with one that
fails the test if it is ever called.
"""

from __future__ import annotations

import os
import subprocess
import sys
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Final

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
_TOOLS_DIR: Final = REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import doc_sweep  # noqa: E402
from toolpath import resolve_tool  # noqa: E402

GIT_TIMEOUT: Final = 60
CLI_TIMEOUT: Final = 120

#: The floor for "the real tree's population is non-trivial". Deliberately far
#: below the measured count so a doc relocation never reddens it; its job is to
#: refuse a sweep that saw nothing, not to restate a count.
REAL_TREE_MARKDOWN_FLOOR: Final = 20

#: The files every synthetic repository starts with - enough for a clean sweep
#: to have a population worth asserting over.
BASE_FILES: Final = {
    "README.md": "# Readme\n\nSee [the guide](docs/guide.md) and `CLAUDE.md`.\n",
    "CLAUDE.md": "# Rules\n\nThe ledger is `docs/ledger.md`.\n",
    "docs/guide.md": "# Guide\n\n## Getting started\n\nBack to [readme](../README.md).\n",
    "docs/ledger.md": "# Ledger\n\nNothing yet.\n",
}
BASE_MARKDOWN_COUNT: Final = len(BASE_FILES)


# --- the throwaway repository ------------------------------------------------


def _git_env() -> dict[str, str]:
    """Return an environment with every inherited ``GIT_`` variable removed.

    A pre-push hook exports ``GIT_DIR``; a child inheriting it would act on the
    real repository. System and global configuration are switched off so an
    ambient hooks path, signing rule or template cannot reach the plant.
    """
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    return env


def _git(root: Path, *args: str) -> None:
    """Run git in ``root`` and fail the test on a non-zero exit."""
    git = resolve_tool("git")
    if git is None:
        pytest.skip("git is not on PATH; the throwaway repository cannot be built")
    completed = subprocess.run(
        [
            git,
            "-C",
            str(root),
            "-c",
            "user.name=doc-sweep-test",
            "-c",
            "user.email=doc-sweep-test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=GIT_TIMEOUT,
        env=_git_env(),
    )
    assert completed.returncode == 0, completed.stderr


def _write(root: Path, files: dict[str, str]) -> None:
    """Write ``files`` under ``root`` as LF bytes."""
    for name, text in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode("ascii"))


RepoFactory = Callable[..., Path]


@pytest.fixture
def make_repo(tmp_path: Path) -> RepoFactory:
    """Build and COMMIT a synthetic repository: the base files plus ``extra``.

    ``drop`` names base files to leave out; ``untracked`` files are written but
    never added.
    """

    def build(
        extra: dict[str, str] | None = None,
        *,
        drop: tuple[str, ...] = (),
        untracked: dict[str, str] | None = None,
    ) -> Path:
        root = tmp_path / "repo"
        root.mkdir()
        files = {name: text for name, text in BASE_FILES.items() if name not in drop}
        files.update(extra or {})
        _write(root, files)
        _git(root, "init", "-q")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "plant")
        _write(root, untracked or {})
        return root

    return build


def _sweep(root: Path, **kwargs: object) -> doc_sweep.Report:
    """Sweep ``root`` with an empty allowlist unless one is given."""
    kwargs.setdefault("allowlist", {})
    kwargs.setdefault("stale_allowlist", {})
    return doc_sweep.sweep(root, **kwargs)  # type: ignore[arg-type]


def _kinds(report: doc_sweep.Report) -> list[tuple[str, str]]:
    """Return every finding as ``(kind, path)``."""
    return [(finding.kind, finding.path) for finding in report.findings]


# --- the slug rule, pinned on headings from this repository -------------------

# Each heading is copied verbatim from a tracked file in this repository; the
# comment names where. The expected fragment is GitHub's rule applied by hand:
# lowercase, drop every character that is not a letter, digit, space, hyphen or
# underscore, then each space becomes one hyphen - so " - " becomes "---".
REPO_HEADING_SLUGS: Final = (
    # CLAUDE.md - backticks and a dotted section number.
    (
        "2.1 Module map - one line each, detail in `docs/ARCHITECTURE.md`",
        "21-module-map---one-line-each-detail-in-docsarchitecturemd",
    ),
    # CLAUDE.md - a dotted number and an ISO date.
    (
        "6.1 Authority - filed 2026-09-13 by operator directive",
        "61-authority---filed-2026-09-13-by-operator-directive",
    ),
    # docs/OPERATIONS.md - a trailing dot, a colon and a code span.
    ("10. Runbook: the headless `queue` lane", "10-runbook-the-headless-queue-lane"),
    # docs/history_notes.md - intraword underscores survive, dots and slashes do not.
    (
        "CS-1060 - RELOCATED 2026-09-14 on closure, from docs/item_notes/phase4-followups-900.md",
        "cs-1060---relocated-2026-09-14-on-closure-from-docsitem_notesphase4-followups-900md",
    ),
    # docs/item_notes/phase7.md - a code span holding a hex identifier.
    (
        "FILED 2026-09-24, from the N0 adjudicator ruling at `599528c`",
        "filed-2026-09-24-from-the-n0-adjudicator-ruling-at-599528c",
    ),
)


@pytest.mark.parametrize(("heading", "expected"), REPO_HEADING_SLUGS)
def test_a_repo_heading_slugs_to_the_github_fragment(heading: str, expected: str) -> None:
    assert doc_sweep.Slugger().slug(heading) == expected


def test_a_repeated_heading_takes_numbered_suffixes_in_document_order() -> None:
    # docs/item_notes/phase7.md repeats both of these headings, once per item.
    slugger = doc_sweep.Slugger()
    got = [
        slugger.slug(text)
        for text in (
            "Acceptance",
            "NOTE - relocated from `ROADMAP.md` 2026-08-23",
            "Acceptance",
            "NOTE - relocated from `ROADMAP.md` 2026-08-23",
            "Acceptance",
        )
    ]
    assert got == [
        "acceptance",
        "note---relocated-from-roadmapmd-2026-08-23",
        "acceptance-1",
        "note---relocated-from-roadmapmd-2026-08-23-1",
        "acceptance-2",
    ]


def test_a_suffix_that_collides_with_a_real_heading_is_skipped_past() -> None:
    # The GitHub slugger re-checks a suffixed slug against every slug already
    # issued, so a literal "a-1" heading pushes the next duplicate further on.
    slugger = doc_sweep.Slugger()
    assert [slugger.slug(t) for t in ("a", "a", "a-1")] == ["a", "a-1", "a-1-1"]


def test_a_suffix_already_issued_is_skipped_past_on_a_later_duplicate() -> None:
    slugger = doc_sweep.Slugger()
    assert [slugger.slug(t) for t in ("a", "a-1", "a")] == ["a", "a-1", "a-2"]


def test_heading_markup_renders_before_it_slugs() -> None:
    slugger = doc_sweep.Slugger()
    assert slugger.slug("See [the guide](docs/guide.md) and **bold**") == "see-the-guide-and-bold"
    assert slugger.slug("An _emphasised_ word and a snake_case name") == (
        "an-emphasised-word-and-a-snake_case-name"
    )


def test_anchors_read_atx_setext_and_html_ids_and_skip_fences() -> None:
    text = (
        "# Title #\n"
        "\n"
        "Setext heading\n"
        "==============\n"
        "\n"
        "```\n"
        "# not a heading\n"
        "```\n"
        '<a id="explicit"></a>\n'
        "## Title\n"
    )
    assert doc_sweep.anchors(text) == {"title", "setext-heading", "explicit", "title-1"}


# --- the CS-1184 repair: headings GitHub anchors, and regions it never renders --


def test_a_two_line_setext_heading_is_one_anchor() -> None:
    # The softbreak renders as a newline, which the character rule drops.
    assert doc_sweep.anchors("Line one\nLine two\n========\n") == {"line-oneline-two"}


def test_a_heading_inside_a_blockquote_or_a_list_item_is_anchored() -> None:
    # GitHub renders both as h2 elements and anchors every heading element.
    text = "> ## Quoted\n\n- ## Listed\n\n1. ### Numbered\n\n> Quoted setext\n> ---\n"
    assert doc_sweep.anchors(text) == {"quoted", "listed", "numbered", "quoted-setext"}


def test_a_line_outside_a_quote_is_not_a_setext_underline_for_it() -> None:
    # The dashes cannot continue the quote lazily; they are a thematic break.
    assert doc_sweep.anchors("> quote\n---\n") == set()


def test_a_list_item_followed_by_dashes_is_not_a_setext_heading() -> None:
    assert doc_sweep.anchors("- item\n---\n") == set()


def test_an_autolink_in_a_heading_keeps_its_text() -> None:
    assert doc_sweep.Slugger().slug("See <https://x>") == "see-httpsx"


def test_an_unpaired_underscore_survives_the_slug() -> None:
    slugger = doc_sweep.Slugger()
    assert slugger.slug("The _private prefix") == "the-_private-prefix"
    assert slugger.slug("A __dunder__ name") == "a-dunder-name"


def test_nested_underscore_emphasis_is_unwrapped_to_its_text() -> None:
    # Renders as <em>outer and <strong>inner</strong> word</em>.
    assert doc_sweep.Slugger().slug("_outer and __inner__ word_") == "outer-and-inner-word"


def test_a_heading_inside_an_html_comment_is_no_anchor() -> None:
    text = "<!--\n# Hidden\n-->\n# Shown <!-- # also hidden -->\n<!-- # inline hidden -->\n"
    assert doc_sweep.anchors(text) == {"shown"}


def test_yaml_front_matter_is_no_anchor() -> None:
    text = "---\nname: agent\ndescription: x\n---\n# Real\n"
    assert doc_sweep.anchors(text) == {"real"}


def test_a_comment_opener_inside_a_code_span_is_literal() -> None:
    assert doc_sweep.anchors("Write `<!--` to open one.\n\n# After\n") == {"after"}


# --- the population ----------------------------------------------------------


def test_a_clean_synthetic_repository_sweeps_clean_over_a_real_population(
    make_repo: RepoFactory,
) -> None:
    report = _sweep(make_repo())
    assert report.findings == []
    assert report.markdown_files == BASE_MARKDOWN_COUNT


def test_the_real_tree_sweep_sees_a_non_trivial_population() -> None:
    report = doc_sweep.sweep(REPO_ROOT)
    scanned = report.markdown_files
    assert scanned >= REAL_TREE_MARKDOWN_FLOOR


def test_an_untracked_plant_is_outside_the_population(make_repo: RepoFactory) -> None:
    report = _sweep(make_repo(untracked={"docs/stray.md": "# Stray\n"}))
    assert report.findings == []
    assert report.markdown_files == BASE_MARKDOWN_COUNT


def test_a_repository_with_no_tracked_markdown_could_not_run(make_repo: RepoFactory) -> None:
    root = make_repo({"src/x.py": "x = 1\n"}, drop=tuple(BASE_FILES))
    with pytest.raises(doc_sweep.CouldNotRunError, match="no tracked markdown"):
        _sweep(root)


def test_a_directory_that_is_not_a_repository_could_not_run(tmp_path: Path) -> None:
    _write(tmp_path, {"README.md": "# x\n"})
    with pytest.raises(doc_sweep.CouldNotRunError):
        _sweep(tmp_path)


def test_a_subdirectory_of_a_work_tree_could_not_run(make_repo: RepoFactory) -> None:
    root = make_repo()
    with pytest.raises(doc_sweep.CouldNotRunError, match="not its top level"):
        _sweep(root / "docs")


# --- orphans -----------------------------------------------------------------


def test_a_synthetic_orphan_is_reported_red(make_repo: RepoFactory) -> None:
    report = _sweep(make_repo({"docs/orphan.md": "# Orphan\n\nLinks out to `CLAUDE.md`.\n"}))
    assert _kinds(report) == [(doc_sweep.ORPHAN, "docs/orphan.md")]


def test_a_backticked_path_mention_is_a_reference(make_repo: RepoFactory) -> None:
    extra = {
        "docs/cited.md": "# Cited\n",
        "docs/guide.md": BASE_FILES["docs/guide.md"] + "\nSee `docs/cited.md`.\n",
    }
    assert _sweep(make_repo(extra)).findings == []


def test_a_link_relative_to_the_referring_file_is_a_reference(make_repo: RepoFactory) -> None:
    extra = {
        "docs/sub/leaf.md": "# Leaf\n",
        "docs/guide.md": BASE_FILES["docs/guide.md"] + "\n[leaf](sub/leaf.md)\n",
    }
    assert _sweep(make_repo(extra)).findings == []


def test_a_mention_in_a_code_file_is_a_reference(make_repo: RepoFactory) -> None:
    extra = {"docs/pinned.md": "# Pinned\n", "tools/pin.py": 'DOC = "docs/pinned.md"\n'}
    assert _sweep(make_repo(extra)).findings == []


@pytest.mark.parametrize(
    "hiding",
    [
        "\n```\ncat docs/hidden.md\n```\n",
        "\n~~~~\n[x](docs/hidden.md)\n~~~~\n",
        "\n<!-- see docs/hidden.md -->\n",
        "\n<!--\n[x](docs/hidden.md)\n-->\n",
    ],
    ids=["backtick-fence", "tilde-fence", "inline-comment", "multiline-comment"],
)
def test_a_mention_nobody_can_follow_is_not_a_reference(
    make_repo: RepoFactory, hiding: str
) -> None:
    extra = {"docs/hidden.md": "# Hidden\n", "README.md": BASE_FILES["README.md"] + hiding}
    assert _kinds(_sweep(make_repo(extra))) == [(doc_sweep.ORPHAN, "docs/hidden.md")]


def test_a_mention_after_a_closed_comment_on_its_line_is_a_reference(
    make_repo: RepoFactory,
) -> None:
    extra = {
        "docs/shown.md": "# Shown\n",
        "README.md": BASE_FILES["README.md"] + "\n<!--\nx\n--> see `docs/shown.md`\n",
    }
    assert _sweep(make_repo(extra)).findings == []


def test_an_empty_comment_closes_itself(make_repo: RepoFactory) -> None:
    # CommonMark closes "<!-->" and "<!--->" at once; the mention after each is visible.
    extra = {
        "docs/shown.md": "# Shown\n",
        "docs/also.md": "# Also\n",
        "README.md": BASE_FILES["README.md"]
        + "\n<!--> see `docs/shown.md`\n\n<!---> see `docs/also.md`\n",
    }
    assert _sweep(make_repo(extra)).findings == []


def test_a_fragment_inside_an_html_comment_is_not_a_link(make_repo: RepoFactory) -> None:
    extra = {"README.md": BASE_FILES["README.md"] + "\n<!-- [x](docs/guide.md#gone) -->\n"}
    report = _sweep(make_repo(extra))
    assert report.findings == []
    assert report.fragments_checked == 0


def test_an_unreferenced_archive_file_is_not_an_orphan(make_repo: RepoFactory) -> None:
    report = _sweep(make_repo({"docs/_archive/old-2026-01-01.md": "# Old\n"}))
    assert report.findings == []


def test_an_archive_file_is_not_a_root(make_repo: RepoFactory) -> None:
    extra = {"docs/_archive/old.md": "# Old\n\n[leaf](../leaf.md)\n", "docs/leaf.md": "# Leaf\n"}
    assert _kinds(_sweep(make_repo(extra))) == [(doc_sweep.UNREACHABLE, "docs/leaf.md")]


def test_an_archive_file_still_has_its_anchors_checked(make_repo: RepoFactory) -> None:
    extra = {"docs/_archive/old.md": "# Old\n\n[x](../guide.md#gone)\n"}
    assert _kinds(_sweep(make_repo(extra))) == [(doc_sweep.DEAD_ANCHOR, "docs/_archive/old.md")]


def test_the_tail_of_a_url_is_not_a_repository_path(make_repo: RepoFactory) -> None:
    # The query value is the plant: "=/" breaks the run of path characters, so
    # only the refusal to start a token after "/" keeps it from resolving. A
    # plain "host/docs/orphan.md" tail never exercises that refusal - the match
    # starts at the host and resolves to nothing - and a mutant removing it
    # survived that plant.
    extra = {
        "docs/orphan.md": "# Orphan\n",
        "README.md": BASE_FILES["README.md"]
        + "\n<https://example.invalid/view?file=/docs/orphan.md>\n",
    }
    assert _kinds(_sweep(make_repo(extra))) == [(doc_sweep.ORPHAN, "docs/orphan.md")]


def test_a_self_reference_does_not_rescue_an_orphan(make_repo: RepoFactory) -> None:
    extra = {"docs/self.md": "# Self\n\nSee [me](self.md) and `docs/self.md`.\n"}
    assert _kinds(_sweep(make_repo(extra))) == [(doc_sweep.ORPHAN, "docs/self.md")]


def test_an_island_referenced_only_by_itself_is_unreachable(make_repo: RepoFactory) -> None:
    extra = {
        "docs/island_a.md": "# A\n\n[b](island_b.md)\n",
        "docs/island_b.md": "# B\n\n[a](island_a.md)\n",
    }
    assert sorted(_kinds(_sweep(make_repo(extra)))) == [
        (doc_sweep.UNREACHABLE, "docs/island_a.md"),
        (doc_sweep.UNREACHABLE, "docs/island_b.md"),
    ]


def test_a_file_reached_only_through_an_orphan_is_unreachable(make_repo: RepoFactory) -> None:
    extra = {"docs/orphan.md": "# O\n\n[leaf](leaf.md)\n", "docs/leaf.md": "# Leaf\n"}
    assert sorted(_kinds(_sweep(make_repo(extra)))) == [
        (doc_sweep.ORPHAN, "docs/orphan.md"),
        (doc_sweep.UNREACHABLE, "docs/leaf.md"),
    ]


def test_the_allowlist_names_an_orphan_out_of_the_report(make_repo: RepoFactory) -> None:
    root = make_repo({"docs/orphan.md": "# Orphan\n\n[leaf](leaf.md)\n", "docs/leaf.md": "# L\n"})
    report = _sweep(root, allowlist={"docs/orphan.md": "loaded by convention"})
    assert report.findings == []


def test_an_allowlisted_directory_prefix_covers_its_members(make_repo: RepoFactory) -> None:
    root = make_repo({".claude/agents/a.md": "# A\n", ".claude/agents/b.md": "# B\n"})
    report = _sweep(root, allowlist={".claude/agents/": "loaded by the harness"})
    assert report.findings == []


def test_an_allowlist_entry_matching_nothing_is_stale(make_repo: RepoFactory) -> None:
    report = _sweep(make_repo(), allowlist={"docs/gone.md": "was a root once"})
    assert _kinds(report) == [(doc_sweep.STALE_EXCUSE, "docs/gone.md")]


def test_the_manifest_does_not_count_as_a_reference(make_repo: RepoFactory) -> None:
    extra = {
        "docs/orphan.md": "# Orphan\n",
        "tools/provenance.tsv": "docs/orphan.md\tauthored\tCS-1\tstamped\n",
    }
    assert _kinds(_sweep(make_repo(extra))) == [(doc_sweep.ORPHAN, "docs/orphan.md")]


def test_an_unreferenced_root_is_not_an_orphan(make_repo: RepoFactory) -> None:
    # README.md names CLAUDE.md in the base set; drop that mention.
    extra = {"README.md": "# Readme\n\nSee [the guide](docs/guide.md).\n"}
    assert _sweep(make_repo(extra)).findings == []


# --- anchors -----------------------------------------------------------------


def test_a_synthetic_dead_anchor_is_reported_red(make_repo: RepoFactory) -> None:
    extra = {"README.md": BASE_FILES["README.md"] + "\n[x](docs/guide.md#no-such-heading)\n"}
    report = _sweep(make_repo(extra))
    assert _kinds(report) == [(doc_sweep.DEAD_ANCHOR, "README.md")]
    assert "docs/guide.md#no-such-heading" in report.findings[0].detail


def test_a_dead_same_file_anchor_is_reported_red(make_repo: RepoFactory) -> None:
    extra = {"docs/ledger.md": "# Ledger\n\nSee [above](#ledgers).\n"}
    assert _kinds(_sweep(make_repo(extra))) == [(doc_sweep.DEAD_ANCHOR, "docs/ledger.md")]


def test_a_live_anchor_is_clean_and_counted(make_repo: RepoFactory) -> None:
    extra = {
        "README.md": BASE_FILES["README.md"]
        + "\n[a](docs/guide.md#getting-started) [b](#readme) [c](CLAUDE.md#rules)\n",
    }
    report = _sweep(make_repo(extra))
    assert report.findings == []
    assert report.fragments_checked == len(("a", "b", "c"))


def test_a_reference_definition_fragment_is_checked(make_repo: RepoFactory) -> None:
    extra = {"README.md": BASE_FILES["README.md"] + "\n[ref]: docs/guide.md#gone\n"}
    assert _kinds(_sweep(make_repo(extra))) == [(doc_sweep.DEAD_ANCHOR, "README.md")]


def test_a_fragment_inside_a_fence_or_code_span_is_not_a_link(make_repo: RepoFactory) -> None:
    extra = {
        "README.md": BASE_FILES["README.md"]
        + "\n```\n[x](docs/guide.md#gone)\n```\n\n`[y](docs/guide.md#gone)`\n",
    }
    report = _sweep(make_repo(extra))
    assert report.findings == []
    assert report.fragments_checked == 0


def test_a_fragment_into_a_non_markdown_target_is_skipped_and_counted(
    make_repo: RepoFactory,
) -> None:
    extra = {
        "tools/x.py": "x = 1\n",
        "README.md": BASE_FILES["README.md"] + "\n[x](tools/x.py#L1) `tools/x.py`\n",
    }
    report = _sweep(make_repo(extra))
    assert report.findings == []
    assert report.skips.get(doc_sweep.SKIP_NON_MARKDOWN_TARGET) == 1


# --- staleness ---------------------------------------------------------------


def test_a_dated_artifact_outside_the_archive_is_stale(make_repo: RepoFactory) -> None:
    extra = {
        "docs/digest-2026-09-01.md": "# Digest\n",
        "CLAUDE.md": BASE_FILES["CLAUDE.md"] + "`docs/digest-2026-09-01.md`\n",
    }
    assert _kinds(_sweep(make_repo(extra))) == [(doc_sweep.STALE, "docs/digest-2026-09-01.md")]


def test_a_dated_artifact_inside_the_archive_is_not_stale(make_repo: RepoFactory) -> None:
    extra = {
        "docs/_archive/digest-2026-09-01.md": "# Digest\n",
        "CLAUDE.md": BASE_FILES["CLAUDE.md"] + "`docs/_archive/digest-2026-09-01.md`\n",
    }
    assert _sweep(make_repo(extra)).findings == []


def test_a_historical_declaration_outside_the_archive_is_stale(make_repo: RepoFactory) -> None:
    extra = {"docs/ledger.md": "# Ledger\n\n**Section status: HISTORICAL.** Records.\n"}
    assert _kinds(_sweep(make_repo(extra))) == [(doc_sweep.STALE, "docs/ledger.md")]


def test_the_stale_allowlist_names_a_record_out_of_the_report(make_repo: RepoFactory) -> None:
    extra = {"docs/ledger.md": "# Ledger\n\n**Section status: HISTORICAL.** Records.\n"}
    report = _sweep(make_repo(extra), stale_allowlist={"docs/ledger.md": "append-only record"})
    assert report.findings == []


def test_a_live_declaration_is_not_stale(make_repo: RepoFactory) -> None:
    extra = {"docs/ledger.md": "# Ledger\n\n**Section status: LIVE.** Rules.\n"}
    assert _sweep(make_repo(extra)).findings == []


# --- external URLs: tier-3 only, never on push --------------------------------

URL_README: Final = (
    BASE_FILES["README.md"]
    + "\n[ok](https://example.invalid/ok) [dead](https://example.invalid/dead)\n"
    + "<https://example.invalid/ok>\n"
    + "[wiki](https://game.wiki.gg/wiki/Page)\n"
)


def _stub_fetch(calls: list[str]) -> Callable[[str], int]:
    """Return a fetcher that records each URL and answers 404 for ``/dead``."""

    def fetch(url: str) -> int:
        calls.append(url)
        return 404 if url.endswith("/dead") else 200

    return fetch


def test_the_default_path_never_touches_the_network(
    make_repo: RepoFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(*_args: object, **_kwargs: object) -> None:
        pytest.fail("the default sweep reached the network")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    calls: list[str] = []
    report = _sweep(make_repo({"README.md": URL_README}), fetch=_stub_fetch(calls))
    assert calls == []
    assert report.findings == []
    assert report.urls_checked == 0
    assert report.skips.get(doc_sweep.SKIP_EXTERNAL_URL, 0) > 0


def test_the_urls_flag_checks_each_url_once_through_the_fetcher(make_repo: RepoFactory) -> None:
    calls: list[str] = []
    root = make_repo({"README.md": URL_README})
    report = _sweep(root, check_urls=True, fetch=_stub_fetch(calls))
    assert sorted(calls) == ["https://example.invalid/dead", "https://example.invalid/ok"]
    assert _kinds(report) == [(doc_sweep.DEAD_URL, "README.md")]
    assert report.skips.get(doc_sweep.SKIP_NO_FETCH_HOST) == 1


def test_a_badge_yields_both_its_image_and_its_link(make_repo: RepoFactory) -> None:
    badge = "[![ci](https://example.invalid/badge.svg)](https://example.invalid/dead)\n"
    calls: list[str] = []
    root = make_repo({"README.md": BASE_FILES["README.md"] + badge})
    report = _sweep(root, check_urls=True, fetch=_stub_fetch(calls))
    assert sorted(calls) == ["https://example.invalid/badge.svg", "https://example.invalid/dead"]
    assert _kinds(report) == [(doc_sweep.DEAD_URL, "README.md")]


@pytest.mark.parametrize("error", [OSError("unreachable"), RuntimeError("bad status line")])
def test_a_fetcher_that_raises_is_a_dead_url(make_repo: RepoFactory, error: Exception) -> None:
    def broken(_url: str) -> int:
        raise error

    extra = {"README.md": BASE_FILES["README.md"] + "\n<https://example.invalid/x>\n"}
    report = _sweep(make_repo(extra), check_urls=True, fetch=broken)
    assert _kinds(report) == [(doc_sweep.DEAD_URL, "README.md")]


# --- the CLI contract CS-1183's tier-3 job codes against ----------------------


def test_main_exits_one_on_findings_and_prints_the_skip_count(
    make_repo: RepoFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_repo({"docs/orphan.md": "# Orphan\n"})
    code = doc_sweep.main(["--root", str(root)])
    out = capsys.readouterr().out
    assert code == doc_sweep.EXIT_FINDINGS
    assert "ORPHAN docs/orphan.md" in out
    assert "skipped: " in out
    assert str(root) not in out


def test_main_exits_zero_when_clean(
    make_repo: RepoFactory, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # The real tables name files a synthetic repository does not carry, and an
    # entry matching nothing is itself a finding - so they are emptied here.
    monkeypatch.setattr(doc_sweep, "ALLOWLIST", {})
    monkeypatch.setattr(doc_sweep, "STALE_ALLOWLIST", {})
    code = doc_sweep.main(["--root", str(make_repo())])
    out = capsys.readouterr().out
    assert code == doc_sweep.EXIT_CLEAN
    assert "findings: 0" in out


def test_main_exits_two_when_it_could_not_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = doc_sweep.main(["--root", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == doc_sweep.EXIT_COULD_NOT_RUN
    assert str(tmp_path) not in captured.out + captured.err


def test_main_urls_flag_reaches_the_fetcher(
    make_repo: RepoFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[str] = []
    root = make_repo({"README.md": URL_README})
    code = doc_sweep.main(["--root", str(root), "--urls"], fetch=_stub_fetch(calls))
    out = capsys.readouterr().out
    assert code == doc_sweep.EXIT_FINDINGS
    assert calls
    assert "DEAD-URL README.md" in out


def test_the_script_runs_as_a_subprocess_with_the_published_exit_code(
    make_repo: RepoFactory,
) -> None:
    root = make_repo({"docs/orphan.md": "# Orphan\n"})
    completed = subprocess.run(
        [sys.executable, str(_TOOLS_DIR / "doc_sweep.py"), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
        timeout=CLI_TIMEOUT,
        env=_git_env(),
    )
    assert completed.returncode == doc_sweep.EXIT_FINDINGS, completed.stderr
    assert "ORPHAN docs/orphan.md" in completed.stdout


def test_every_named_allowlist_entry_carries_a_reason() -> None:
    for table in (
        doc_sweep.ROOTS,
        doc_sweep.ALLOWLIST,
        doc_sweep.STALE_ALLOWLIST,
        doc_sweep.REFERRER_EXCLUDED,
        doc_sweep.NO_FETCH_HOSTS,
    ):
        empty = [name for name, reason in table.items() if not reason.strip()]
        assert empty == []
