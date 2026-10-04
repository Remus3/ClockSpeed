# Public readiness - pre-publication audit

**Section status: LIVE.** A point-in-time audit of what would become public if this
repository were published, written for the operator ahead of the visibility flip. The
gate itself is CS-G03 in `docs/GATED.md` and the plan that runs it is CS-700 in
`docs/item_notes/phase7.md`; this file records findings and recommended fixes and
decides nothing those two own.

Measured on 2026-10-03 against local `main` at `29d0cd9` and against every ref the
remote currently serves.

---

## Verdict

**NOT READY to flip by toggling visibility.** The tree and its history are clean of
secrets, personal data needles, publisher-owned assets and binaries. The blockers are all
in git METADATA and in the remote's ref set, and every one of them is already handled by
the CS-700 plan - which deletes and recreates the remote and pushes a rewritten `main`
rather than switching the existing repository to public.

| Severity | Count | Summary |
|---|---|---|
| BLOCKER | 3 | Personal email in commit identities; non-`main` refs on the remote; agent co-authorship trailers |
| MEDIUM | 2 | Private vulnerability reporting off; secret scanning and push protection unavailable while private |
| LOW | 3 | Machine layout paths in docs; one non-public sibling project named in archive docs; tier1 badge red |
| CLEAR | 7 | Secrets, PII needles, licences, publisher assets, binaries, README walk, clean checkout |

**Recommended route:** run CS-700 as planned. Do NOT use the GitHub "Change visibility"
button on the current remote - that publishes every finding in the BLOCKER rows at once,
and none of them can be withdrawn afterwards, because anyone can clone in the meantime.

---

## Method

1. `python tools/flip_checks.py HEAD --stage s1` - the seven tier-3 flip checks plus the
   trailer axis, run by hand on this machine as ADR 0025 requires. Automated verdict PASS,
   0 of 8 automated checks failed; the two human halves are NOT-RUN-HERE (CS-1186 and
   CS-1187, gated under CS-G08). Its secret scan covered every blob and every commit
   message reachable from `main`; its PII scan used needles derived in-process from this
   machine's account directory, Windows account, home paths and save header.
2. A second, independent regex sweep over every blob reachable from ANY ref the remote
   serves (not only `main`): provider key shapes (Anthropic, OpenAI, GitHub, AWS, Google,
   Slack), private-key headers, the operator's personal email, a Windows home path and
   tailnet addresses. Commit messages were swept for the same patterns.
3. `git ls-remote origin` for the ref set, `git log --format` for identities, and
   `git cat-file --batch-check` for blob sizes and path history.
4. `python tools/doc_sweep.py --urls` over the working tree, after the README refresh.
5. `gh api` for the repository's feature and security settings.

No gitleaks or trufflehog is installed on this machine; steps 1 and 2 stand in for them.

---

## BLOCKER findings

### B1 - Personal email in commit identities

The commits reachable from the remote's refs are authored and committed under two
identities: the GitHub noreply address and a personal email address. The personal
address appears as author and committer on 588 of them (520 on local `main`). A public
repository exposes this to anyone who clones it or opens a commit's `.patch` view.

**Fix:** CS-700 step S7a rewrites author and committer on every `main` commit to the
chosen noreply identity, and S8 re-scans to prove it. History rewrite was NOT done by
this audit. The population is closed: every commit since 2026-09-07 already uses the
noreply identity, so S7a has a fixed set to rewrite.

### B2 - The remote serves far more than `main`

Besides `main`, the remote holds 12 other branches (diagnostic branches, a WIP branch,
the `lane/queue` lane branch and four `worktree-agent-*` branches), 5 `salvage/*` tags
and 53 refs under `refs/wip/`. 68 commits are reachable only from those refs. A
`refs/wip/*` ref does not show in the web UI but is served to any `git clone --mirror`.
The flip checks grade `main` only, so nothing on these refs has been through the PII
gate.

**Fix:** CS-700 step S9 deletes and recreates the remote and S10 pushes only the
adjudicated `main`. If the remote is ever kept instead, every non-`main` ref must be
deleted from it first. The pre-rewrite bundle CS-700 takes at S4/S5 preserves them.

### B3 - Agent co-authorship trailers

18 commits on `main` carry a `Co-authored-by:` trailer naming an agent, all dated
2026-08-14 or 2026-08-15. The 2026-08-13 operator decision in `docs/GATED.md` forbids
them in published history; the commit-msg hook has refused new ones since. The flip
checks' trailer axis found exactly these 18, all strippable.

**Fix:** CS-700 step S7a strips them; S8 proves zero remain.

---

## MEDIUM findings

### M1 - Private vulnerability reporting is off

`.github/SECURITY.md` routes reports through GitHub private vulnerability reporting and
deliberately carries no email address. The setting cannot be enabled while the
repository is private (the API answers 404), so on the day of the flip the security
policy would point at a disabled channel.

**Fix (operator, immediately after the flip):** Settings > Code security > Private
vulnerability reporting > Enable, or
`gh api -X PUT repos/Remus3/Clockspeed/private-vulnerability-reporting`.

### M2 - Secret scanning and push protection are unavailable while private

The API refuses to enable secret scanning on this private repository on the current
plan. Both are free on a public repository. The tier-0 commit gate already scans for
secrets locally, so this is a second layer, not the only one.

**Fix (operator, immediately after the flip):** Settings > Code security > enable Secret
scanning and Push protection.

---

## LOW findings

### L1 - Machine layout paths in tracked docs and code

No home path, account name or user directory appears anywhere: every `C:/Users/` hit is
a placeholder or a synthetic test token. What does appear is machine layout outside the
home directory: the lane worktree base under a `C:\` root folder in `ops/loop/` and
`docs/OPERATIONS.md`, a `C:\ProgramData` slot directory in `ops/loop/slots.py`, the
location of the pre-rewrite bundle in `docs/LEDGER.md`, and default Program Files
install paths in `BOOTSTRAP.md`. None is personal data and the code ones are defaults a
user can override.

**Fix:** none required. Optional: leave as is.

### L2 - A non-public sibling project named in archive docs

The sibling repositories this project vendors from or cites by name are public, so
naming them is not a leak. One sibling project that is NOT published is named in full in
a few lines of `docs/LEDGER.md` and `docs/history_notes.md`, where cross-project hook
and port measurements were recorded. The cross-repository channel document itself names
participants only by short code.

**Fix:** optional. `docs/LEDGER.md` is append-only, so a redaction would be a new
superseding record or part of the S7a rewrite, not an in-place edit.

### L3 - The tier1 badge will render red

The README's tier1 badge reflects the latest run on `main`, which failed at the time of
this audit. On a public page that is the first thing a visitor sees.

**Fix:** get tier1 green on the SHA that is published.

---

## CLEAR

| Axis | Result |
|---|---|
| Secrets | Flip check 1: 0 findings over every blob and commit message on `main`. Independent sweep over every remote ref: one AWS-key-shaped hit, AWS's own documented example key, used as a scanner test case - not a credential. A commit message that mentions a credential PREFIX carries no key. |
| PII needles | Flip check 2: 0 blob, path or commit hits. |
| Third-party licences | Flip check 3: PASS. Vendored files are listed in `THIRD_PARTY.md`. |
| Publisher-owned assets and saves | Flip check 4: 0 publisher paths in all of history. No `.sav`, `.pak`, `.usmap`, image, archive, certificate or executable path has ever been on any remote ref. |
| Large binaries | None. The largest blobs on any remote ref are revisions of `docs/LEDGER.md`, under 2 MB each, all text. |
| README walk | Flip check 5 automated half: PASS. |
| Clean checkout | Flip check 7 automated half: PASS. |
| Doc links | `tools/doc_sweep.py --urls`: 0 findings other than the two tier1 badge URLs, which 404 only while the repository is private and are pinned as such by ADR 0025. |

---

## GitHub settings - state, and what to re-apply after S9

S9 recreates the remote, which discards every repository-level setting below. Re-apply
them on the new repository after S10.

| Setting | State now | Done by |
|---|---|---|
| Description | Set | Kept as is |
| Topics | 20 set, GitHub's maximum | Kept as is |
| Homepage | Empty - there is no Pages site | - |
| Wiki | Disabled (it was enabled and empty) | This audit |
| Projects | Disabled | This audit |
| Discussions | Disabled - nothing in `.github/CONTRIBUTING.md` routes to them | Unchanged |
| Issues | Enabled, with an issue form and a config pointing at `/api/health` and the ADRs | Unchanged |
| Dependabot alerts | Enabled | This audit |
| Dependabot security update PRs | Disabled - history is linear and lands by cherry-pick, never by merge | Unchanged |
| Secret scanning, push protection | Unavailable while private | Operator, after the flip (M2) |
| Private vulnerability reporting | Unavailable while private | Operator, after the flip (M1) |
| Branch protection | None on the old remote | CS-700 S11: deletion and non-fast-forward blocked on main only - no required reviews or checks, so the lane's fast-forward pushes land |
| Community profile | health_percentage 100, but the API row `files.issue_template` read null - the API counts only the legacy `.github/ISSUE_TEMPLATE.md`, now added; the row is re-read after the push | CS-959 |
| Social preview image | Not set - the API cannot set it | Operator, manual |

**Social preview.** A 1280x640 PNG is generated at `data/social-preview.png`, which is
gitignored, so no binary enters history. Upload it at Settings > General > Social
preview.

---

## Operator steps, in order

1. Do not toggle visibility on the current remote. Run CS-700 (S7a rewrite, S8 re-scan,
   S9 recreate, S10 push `main` only, S12 publish), which needs your own-words
   confirmation before S9.
2. After publication: enable private vulnerability reporting, secret scanning and push
   protection.
3. Re-apply the settings table above on the recreated repository.
4. Upload `data/social-preview.png` as the social preview.
