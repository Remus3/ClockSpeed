---
description: Grounded activity report read from git plus the ledger plus the roadmap - never from transcript inference.
argument-hint: [window, e.g. 7d | since CS-010 | last-session]
---

# /insights

Window: $ARGUMENTS (default: since the last entry in `docs/LEDGER.md`)

**Every number and every claim in this report comes from git, `docs/LEDGER.md`,
`ROADMAP.md`, `BACKLOG.md`, `docs/GATED.md` or a live command. NEVER from transcript
inference.** What you remember happening is not evidence. If it is not in the artifact, it
did not happen for the purposes of this report - and that gap is itself the most useful
finding, because it means work landed without a ledger entry.

## 1. Read the sources - artifact only

- [ ] `git log --oneline --no-merges` over the window. Commits, dates, item IDs cited.
- [ ] `git diff --stat` over the window. Files touched, lines added and removed.
- [ ] `git log --diff-filter=A --name-only` over the window. Files ADDED.
- [ ] `docs/LEDGER.md` entries in the window - newest-first, one per closed item.
- [ ] `ROADMAP.md` - open items with IDs and acceptance criteria.
- [ ] `BACKLOG.md` - aspirational items and conditional triggers.
- [ ] `docs/GATED.md` - blocked items and their external unblocking conditions.
- [ ] `docs/adr/README.md` - decisions recorded in the window.
- [ ] A LIVE suite run for the current test counts, if you are going to state one.

## 2. Cross-check the sources against each other

The mismatches are the report's real value.

- [ ] Ledger entries with NO corresponding commit in the window - a claim with no artifact.
- [ ] Commits with no ledger entry and no item ID - work that landed unrecorded. Name the
      commits.
- [ ] Items still in `ROADMAP.md` whose acceptance criterion the artifact says is already
      met - closed work sitting in the open file.
- [ ] Items in `docs/LEDGER.md` still listed as open in `ROADMAP.md`.
- [ ] Gated items whose external condition has actually changed.
- [ ] Backlog conditional triggers that have fired.
- [ ] ADR-worthy decisions visible in the diff with no ADR filed.
- [ ] **A ledger entry citing only a commit SHA is fragile** - worktree-agent commits often do
      not survive cherry-pick. Flag any entry that does not cite the item ID, the merged file
      AND the test name.

## 3. Rules for every number you print

- [ ] **Re-derive it from the artifact.** A filed count is a hypothesis, not a fact - filed
      counts have been wrong by an order of magnitude, and rows have refuted their own
      author.
- [ ] Test counts come from a suite run YOU performed this session, with the command and the
      exit code printed beside them. Never a ledger number, never a remembered number, never
      a subagent-reported number.
- [ ] State the SET behind every count. "12 items closed" is meaningless without the window
      and the filter.
- [ ] If a number cannot be derived from an artifact, do not print it. Print the gap instead.
- [ ] Do not restate a measured number that a doc already owns - link to the owner.

## 4. Report

- **Window** - exact date range and how it was derived.
- **Closed** - item ID, one line, the commit, the merged file and the test name. From the
  ledger, cross-checked against git.
- **Landed but unrecorded** - commits in the window with no ledger entry. Each needs a ledger
  entry or an explanation.
- **Recorded but unlanded** - ledger entries with no artifact. Each is a claim to verify.
- **Open** - item IDs in priority order with acceptance criteria, from `ROADMAP.md`.
- **Gated** - items and the exact external condition each waits on; flag any that changed.
- **Decisions** - ADRs filed in the window, plus decisions visible in the diff with no ADR.
- **Current counts** - test pass / fail / skipped from a live run, with the command and exit
  code.
- **Drift** - guard exit codes from a live run; any doc disagreeing with the artifact.
- **Inference gaps** - everything you could NOT ground in an artifact. Say plainly that these
  are ungrounded rather than presenting them as findings.

Do not editorialise about velocity, momentum or productivity. Report what the artifacts say
and where they disagree.
