# 0018 - The flip recreates the remote and keeps the commit graph

## Status

ACCEPTED 2026-09-08.

## Context

`CONVENTIONS.md` section 17 ends with a clause this project had never answered:
**if history is dirty, the honest fix is a fresh-history public repo, not a
rewrite that will be incomplete.** CS-700 required that the choice be made
deliberately and recorded, rather than discovered midway. RC ran the rewrite
branch on 2026-09-07 and needed two passes plus a delete-and-recreate, which is
the cost this ADR exists to avoid paying twice.

The clause is a CONDITIONAL, and this project had never measured whether its
antecedent fires. Two read-only reconnaissance passes on 2026-09-08 measured it.
Each measurement below carried a positive control in its own command family,
because an empty result and a broken pattern print identically and neither
errors - trap (b) of CS-700 section 2, which is how RC's first deletion pass
reported "remaining: 0" while 13 refs existed.

**Measurement 1 - the publishable commit graph is CLEAN OF CONTENT.** Across six
axes
(personal data, save artifacts, publisher-owned game data, `data/` and
`moon_sync_inbox/` paths, credentials, non-ASCII), in blob content, in tree
paths and in commit messages as three separate channels: not one hit is
reachable from `main`, from any `refs/remotes/origin/*`, or from any `salvage/*`
tag. Present-token controls returned 1700 and 772 blobs; absent-token negative
controls returned 0 on the same pass; path controls returned 84 `.md` and 178
`.py`; the commit-message control returned 613 of 682. A full six-axis pass over
every object on disk costs about 7 seconds. **Commit AUTHOR and COMMITTER
identity is a fourth channel this measurement did not cover; see the Foreclosed
clause below, where it is the one open blocker.**

**Measurement 2 - the dirt that exists is off-main and local-only.** It sits in
exactly two buckets: the 4-commit local branch `archive/local-history`, which is
the deliberately retained pre-scrub history and carries 3 blobs across 2 paths;
and 76 ref-less commit objects with 79 pathless blobs that no push and no clone
transfers and that `git gc --prune` deletes. Neither bucket has ever been
pushed.

**Measurement 3 - the remote carries far more than the graph.** 53
`refs/wip/*` refs, 53 distinct SHAs, none an ancestor of `main`; 5 `salvage/*`
tags; 5 non-`main` branches; 233 Actions run records with their logs, 21 of them
failed runs; 17 live artifacts; 11 caches totalling about 534 MiB. **Every one
of these survives a force-push of rewritten history.**

**CORRECTED 2026-09-08, same session, after refutation.** A first version of this
measurement asserted that the 53 wip refs "do not appear in the REST or GraphQL
ref listing, which returns 11". **That is false.** `gh api --paginate` over
`git/refs?per_page=100` returns 64 refs including all 53; the 11 came from an
unpaginated query that returned a short answer without erroring. The refs are
real and the count is right - `git ls-remote origin 'refs/wip/*'` returns 53
against a 6-head control - but the visibility claim was produced by trap (b)
firing inside the evidence offered as proof that trap (b) had been defended
against. The lesson is kept rather than the claim: a positive control proves a
pattern MATCHES and does not prove a query is COMPLETE. Pagination is a second
failure mode needing its own control - compare two command families, not two
patterns. Nothing in the Decision depends on the retracted half.

**Measurement 4 - the forge holds nothing of value to lose.** Zero issues, zero
pull requests, zero releases and assets, zero packages, zero LFS objects, no
wiki content, no Pages, one collaborator, no branch protection and no rulesets.
Trap (d) - deleting a repository deletes its LFS store - does not fire here,
because the store is empty and that was confirmed with a control.

So the antecedent of the section 17 clause does not fire for the commit graph,
and fires decisively for everything the forge has accreted around it. A history
rewrite would be work spent on the one part that is already clean, and would
leave every part that is not. That asymmetry is the whole decision.

Three alternatives were considered and rejected. **Force-push a rewritten
`main`:** rejected, because measurement 3 says it leaves all 53 wip refs, all
233 run logs, the artifacts and the caches standing, and measurement 1 says
there is nothing in `main` for the rewrite to remove. **Prune the remote in
place** - delete the 53 wip refs, the extra branches, the runs, the artifacts
and the caches one namespace at a time: rejected, because it is trap (b)'s
native habitat. It requires a correct deletion pattern and a correct
verification pattern in several different command families, each of which can
fail green, and RC has already demonstrated that exact failure. **Start a
genuinely fresh-history repo,** squashing the whole graph to one commit: rejected, because
it destroys a clean and useful record for no measured benefit, and section 17
prescribes it only as the honest response to dirty history.

## Decision

**The flip recreates the remote and keeps the commit graph.**

The publishable history is `main` exactly as it stands - 521 commits at
`c885879`, unrewritten and unsquashed. The remote repository is deleted and
recreated, and `main` alone is pushed to it. Nothing else is re-pushed by default: not the 53 `refs/wip`
refs, not the `salvage/*` tags, not the non-`main` branches, and never
`archive/local-history`. Every ref other than `main` is preserved locally in a
git bundle before the remote is deleted, so discarding it from the remote loses
no work; any individual ref may then be re-pushed later, but only after it is
measured on all six axes in its own right, one at a time and on the record.

This makes the deletion the verification. Nothing survives that was not
deliberately re-pushed, so no "remaining: 0" claim has to be trusted, and no
deletion pattern has to be correct. That is the property being bought, and it is
bought precisely because measurement 1 says the graph needs no repair.

## Consequences

**Easier.** The flip becomes one push of one measured ref instead of a scrub
plus a rewrite plus several namespace-by-namespace deletions, each needing a
positive control. Trap (b) is designed out rather than defended against: there
is no pattern to get right. Trap (d) is inert, confirmed with a control. The 233
Actions run logs - the highest-risk surface, since 21 are failed runs whose logs
can carry absolute paths, and they are visible to anyone who can see a public
repo - are discarded wholesale rather than audited.

**Harder.** The 53 `refs/wip` refs and the 5 `salvage/*` tags leave the remote.
Anyone wanting one back must fetch it from the bundle and measure it first, and
the bundle is a local artifact that is itself never committed. Repo metadata -
20 topics, 10 labels, description, homepage - and all traffic history are lost
and must be re-entered by hand. The `node_id` changes, so any external reference
to it breaks.

**Foreclosed, AND THE SCOPE OF THIS IS NARROW.** Re-pitching a history rewrite of
`main` **on the grounds that its CONTENT is dirty**. Measurement 1 refutes that,
and re-arguing it requires refuting the controls, not the conclusion.

**This forecloses nothing about commit IDENTITY, which is a fourth channel and is
NOT clean.** Measured at `c885879`: 520 of 521 commits on `main` carry a real
personal email address in both the author and the committer field. `CONVENTIONS`
17 gate item 2 does not reach it - it says tracked files and commit messages, and
identity is neither - and measurement 1 did not look for it. **Whether to publish
under that identity was put to the operator on 2026-09-08 and RULED: rewrite
author and committer across every commit on `main` to a GitHub noreply address.
Accept-as-is and squash-to-fresh-history were both declined.** The mechanics and
the sequencing consequence - every SHA changes, so the preservation bundle must
be taken and proven restorable BEFORE the rewrite - are in CS-700's plan section
6 and step S7a. A rewrite undertaken for that reason is not the rewrite this ADR
rejects, and CS-701 is the same surface already filed.
AMENDED 2026-09-24 by CS-700: the S7a rewrite also STRIPS the agent co-authorship
trailer. Measured at `599528c`, eighteen commits on `main` carry one, oldest
`e9af2df`, newest `5907d45`, one trailer each as the final body line; `docs/GATED.md` CS-G03's eighth
precondition forbids any in the published history, and measurement 1's six axes
never looked for one. The strip removes that line and the blank line before it
and changes nothing else: every other message byte, every tree, every parent
relationship, every date and the commit count are unchanged, so the graph shape
this ADR keeps is kept. It is not a rewrite on CONTENT grounds and reopens
nothing this ADR forecloses; it rides on S7a because S7a already changes every
SHA, so it costs no additional SHA change.

**Revisit if any stated premise changes.** If `main` acquires a dirty commit
after `c885879`, measurement 1 is stale and the six-axis pass must be re-run
before the push - it costs about 7 seconds, so it is re-run immediately before
the flip regardless. If the forge acquires an issue, a pull request, a release,
a star or an LFS object, measurement 4 is stale and delete-and-recreate stops
being free. If anyone pushes `archive/local-history` or a `refs/wip` ref, the
publishable graph is no longer clean and this ADR does not cover the result.

Two limits of measurement 1 are recorded here so they are not mistaken for
coverage. The needles were derived from the save directory **as it exists
today**, so a leak naming a since-deleted world would not have been seen. And
the save header's **player display name was not searched at all**, because
deriving it requires parsing a save, which read-only recon does not do. Both are
carried into the CS-700 plan as work items, not discharged here.

CS-953 is NOT discharged by this decision. It stays open on its own terms: a
filename is not content, and this ADR removes the need for a scrub rather than
proving a scrub correct.
