# CS-1295 repo review findings (session 151)

Section status: HISTORICAL. Review-only findings of the CS-1295 run on branch review/cs1295-s151,
cut at main 726acf1f. Nothing was fixed, deleted or filed; each PROPOSED row is a candidate
BACKLOG.md line with no CS id. KNOWN rows match CS-1291 to CS-1293, an existing BACKLOG line or
docs/_scratch/cs_worktree_classification.md. OPERATOR-GATED rows are irreversible or move a key.

Reading note: authored files were reviewed one row each by foreground sub-agents (slices S01 to
S06e) and every row file was re-counted against its path list. Several slices were judged from
heads, size and a consumer grep rather than full reads (tests, kit files, work/ logs); OK on
those means no defect found at that depth. Per-unit rows for worktrees, nested clones,
duplicate copies and caches (branch, merge status, producer, consumer, verdict) are in the
run data folder, not committed.

## <root-files>

F001 | size budget | CLAUDE.md is 40767 B against a 40960 B hard-fail budget (about 190 B headroom); CONVENTIONS.md is 39788 B. The next CLAUDE.md edit fails CI. Candidate BACKLOG line: relocate a section 7 entry or section 2 prose to docs/history_notes.md before the next edit; never touch the FLEET-COMMON block. | status: PROPOSED

F002 | size budget | BACKLOG.md (76 KB) and THIRD_PARTY.md (71 KB) have no row in tools/doc_budget.py. Candidate BACKLOG line: add budget rows, or split THIRD_PARTY.md per dependency. | status: PROPOSED

F003 | stray file | adj55_node_floor.log: stale ignored root log from an old adjudication; holds a home-directory path and non-ASCII bytes; only docs/LEDGER.md names it. Prune candidate (list only). | status: PROPOSED: move to the sidecar folder or Recycle Bin; OPERATOR-GATED (deletion)

F004 | memory recall | CS-NEXT-SESSION.txt (26 KB, session 151) and WAKEUP_NOTES.md (3 entries, sessions 148-150) are present and current; memory/MEMORY.md lists every leaf on disk. No recall defect in the repo copy. INFERRED: a second, harness-side memory store with about 70 leaves lives outside the repo; it is a candidate for the E:/Sidecars/CS consolidation list and overlaps the repo store in topic. | status: PROPOSED: BACKLOG line recording which store owns which fact class

F005 | pyproject | pyproject.toml is about 1050 lines with a roughly 250-line ruff per-file-ignores block; drift risk, list only. | status: NOT-APPLICABLE: organisation note, no action proposed

## .claude

F006 | worktrees | 21 linked agent worktrees at snapshot (3 pruned by another session mid-run); 18 sit behind main with 1400-1800 commits not in main (cut before the history rewrite), 3 are locked to a live pid. The ancestor test is useless for them; classify by content. | status: KNOWN: CS-1291 item 7 and the BACKLOG old-history linked worktrees line

F007 | worktrees | Three worktrees (a2b6051f, a696864e, ada15e8d) were classed prunable by docs/_scratch/cs_worktree_classification.md in session 100 and still exist. | status: KNOWN: cs_worktree_classification.md (still unactioned)

F008 | runtime | scheduled_tasks.lock is excluded only by .git/info/exclude, so a fresh clone or worktree shows it untracked. Candidate BACKLOG line: add .claude/scheduled_tasks.lock to .gitignore. | status: PROPOSED

F009 | commands | weekly-hygiene.md cites a bare verify_env.py where the path is scripts/verify_env.py. Candidate BACKLOG line: fix the path in .claude/commands/weekly-hygiene.md. | status: PROPOSED

## .git

F010 | git | Root git directory counted as one unit; 100 local branches, including worktree-agent-* branches that match the worktrees. Keep. | status: NOT-APPLICABLE: keep; branch prune is CS-1291 item 7 (KNOWN)

## .githooks

F011 | frozen | pre-push is 43 KB of shell logic in a frozen file; moving logic into tools/ needs a section 6 grant. | status: PROPOSED; OPERATOR-GATED (frozen file)

## .github

F012 | size | tier1.yml (91 KB, 1749 lines) and tier2.yml (61 KB) are single workflow files; maintainability risk, list only. | status: PROPOSED: BACKLOG line to factor shared steps into composite actions

## .mypy_cache / .pytest_cache / .ruff_cache

F013 | generated | Tool caches at the root; regenerable, ignored. | status: NOT-APPLICABLE: regenerable

## <channel inbox folder>

F014 | aggregate | Counted only, never opened. | status: NOT-APPLICABLE: aggregate unit, no review per the rules

## certs

F015 | secrets | dashboard.key.pem (private key) and dashboard.cert.pem sit in an ignored certs/ folder inside the tree, CRLF line endings; regenerable. Not opened. Candidate to move under data/ or a per-user location. | status: PROPOSED; OPERATOR-GATED (a key moves)

## clockspeed

F016 | orphans | clockspeed/solve/bound.py and relax.py have no production importer (tests only). | status: KNOWN: BACKLOG line "From the CS-1244 close" (relax.py); bound.py candidate on the same line

F017 | docs coverage | audit/collectibles.py, audit/footprint.py and data/blobs.py have no docs/ARCHITECTURE.md mention. | status: PROPOSED: BACKLOG line to add module-map rows

F018 | size | save/objects.py (446 KB) and save/world.py (155 KB) are single modules. | status: KNOWN: BACKLOG line on objects.py being the largest module; world.py candidate on the same line

## config

F019 | external path | config/main_tree.local.json (ignored) points at an absolute path on the C: drive that still exists; C:/Clockspeed is a stale old full checkout and old lane logs still reference it. Candidate to consolidate under E:/Sidecars/CS. | status: PROPOSED; OPERATOR-GATED (prune of the old C: checkout)

## corpus

F020 | aggregate | Holds one game-save copy (aggregate row, not named). Personal data, ignored; keep. | status: NOT-APPLICABLE

## data

F021 | dated files | data/ (ignored, 59 files) holds dated scratch with no consumer: 4 session-149 bundles of about 14 MB each, 23 freeze witnesses (sessions 142-149), 16 session 146-147 rulings and specs, 4 session-149 rulings, 5 cs1108 logs from 2026-09, a lane snapshot diff, an unsent ANSWER draft. Archive or prune candidates, list only. Bundles: confirm the landed commits are on the remote first. | status: PROPOSED; OPERATOR-GATED (deletion or archive)

F022 | duplicate | data/social-preview.png and docs/assets/social-preview.png differ in bytes; the README audit test cites both. | status: PROPOSED: BACKLOG line to keep one

## docs

F023 | scratch | docs/_scratch/cs_worktree_classification.md is session 100 and names C: paths that predate ADR 0026; docs/_scratch/cs1087_spec.md is untracked planner scratch whose only reference is history_notes.md. | status: KNOWN (classification doc); cs1087_spec candidate: archive to docs/_archive

F024 | size | docs/history_notes.md is 1.7 MB and names C:/cs-flip-backup and C:/cs-worktrees, which no longer exist; docs/item_notes/phase4.md is 100 KB, check it against the leaf-size rule (ADR 0010/0011). | status: PROPOSED: BACKLOG line to check phase4.md against the leaf rule

## memory

F025 | recall | Repo memory/ has 24 files and an index that lists every leaf; no orphan leaf found. See the root-files memory-recall finding for the second store. | status: NOT-APPLICABLE: no defect

## moon_sync_outbox

F026 | aggregate | Counted only, never opened, treated like the inbox. | status: NOT-APPLICABLE: aggregate unit

## ops

F027 | orphans | ops/fleet_kit/tokens.css and fleet_subagent_status.js have no importer in the tree (vendored, owned by MAIN). | status: NOT-APPLICABLE: vendored kit

F028 | vendored defect | ops/fleet_kit/fleet_headless.py cites docs/rulings/2026-10-10-stale-progress-rows.md, which does not exist (no docs/rulings/ directory). Vendored file: report to MAIN, do not edit. | status: PROPOSED: note to MAIN

F029 | loop control | ops/loop/control/progress/ holds about 290 finished progress files (done or failed) from sessions 141-151, no retention rule and no consumer except the writer; stale rows (cs-1342-land running at 90 percent, cs-s12a-close at 50 percent, failed rows reading pct 100) mislead a live-status reader; 2 files carry CR bytes and 9 pre-push captures are CRLF. | status: KNOWN: CS-1291 item 9 (done files older than 7 days archived); stale running rows PROPOSED

F030 | loop control | Stale lane claims CS-301, CS-870 and CS-892 name a C: worktree that no longer exists; claims.jsonl (323 lines) and subagent_first.jsonl (5.4 MB) have no rotation. | status: PROPOSED: BACKLOG line for claim clearing and log rotation

F031 | loop reports | ops/loop/reports holds 57 old lane_queue logs (53 from 2026-09) with headers pointing at C: paths, 9 reports named by long numeric ids, empty .err files and 2026-09 queue logs; one log points at E:/cs-worktrees/lane-0, outside E:/Sidecars/CS. | status: PROPOSED; OPERATOR-GATED (prune)

F032 | orphan script | ops/loop/control/cs1275_cutover.py is a finished one-shot C-to-E move script that hardcodes C: paths; only history_notes.md mentions it. | status: PROPOSED: move under E:/Sidecars/CS or prune

## scripts

F033 | scripts | 4 authored files, all OK; install_hooks.py is frozen. | status: NOT-APPLICABLE: no defect

## shell

F034 | shell | 20 authored files OK; shell/node_modules (562 files) is a generated unit; keep ignored. | status: NOT-APPLICABLE

## tests

F035 | organisation | tests/ root holds about 14 *_guard.py helpers, a JSON fixture and xdist_quiet.py beside about 120 test files; helpers import from test modules (archive_rot_guard, sphinx_role_guard, the test_queue_loop channel_audit, test_phase4_gate_depth); conftest.py (1.6k lines) is imported as a library for run_git and walk_inventory. | status: PROPOSED: BACKLOG line to create tests/_support and move helpers

F036 | placement | Tests filed under the wrong layer: test_drift_guard_* and test_item_notes_index under tests/data; test_absolute_claims and test_oracle_citations under tests/save; about 12 files named by CS id rather than topic (test_cs1166 to test_cs1329 family). | status: PROPOSED

F037 | size | About a dozen test modules exceed 150 KB (test_docs_citations 232 KB, test_precommit_gate 219 KB, test_queue_loop 210 KB, test_tier1_budget 206 KB, plus save/test_world.py and test_properties.py at 5.6k lines); tests/audit/test_inventory_library.py needs the real save library and skips on a clean clone. | status: PROPOSED: BACKLOG split candidates

## tools

F038 | organisation | tools/ holds data and prose beside code: headless-queue.md (50 KB runbook) and headless-inbox.md (prompt) are not in the CLAUDE.md section 4 owner table; tier1_readings.json (last committed 2026-09-17), tier2_durations.json and measurements.json are data blobs; action_runtimes.py has no caller beyond its test; drift_guard.py (270 KB) and precommit_gate.py (133 KB, frozen) are single modules. | status: PROPOSED: BACKLOG line to add the two .md files to the section 4 table or relocate them

## work

F039 | scratch | work/ (gitignored) holds 1241 flat scratch files from sessions 133-141 (done* logs, s136-s141 logs and scripts, two 25 MB tar snapshots, a 4 MB junk lint log, a stale 115 KB copy of phase7.md), no tracked consumer; the only index is one paragraph in docs/history_notes.md. The group is prunable as a batch. | status: PROPOSED; OPERATOR-GATED (deletion)

F040 | unrecorded rulings | Four ruling files exist only in ignored scratch: s137_rulings.md (header says pending recording), s138_cs1285c_rulings.md, s138_cs1288c_rulings.md, s138_cs1313_rulings.md. Confirm each reached LEDGER or an ADR before any prune; otherwise archive to docs/_archive. Highest-value item in work/. | status: PROPOSED: BACKLOG line

F041 | dead refs | Measure scripts under work/cs1280 and work/cs1286 read a saves folder that no longer exists, so they cannot re-run; work/s137_cs1308_checks.sh points at a worktree path that is gone. About 20 logs match an 8-digit pattern (probably timestamps or CI run ids; values not repeated). | status: NOT-APPLICABLE: ignored scratch

F042 | nested clones | Five full nested clones and five duplicate repo copies live under work/ (about 6900 files); see the R3 unit rows. Consumer check: no tracked file references them except one clone named in one tracked file. | status: KNOWN: CS-1291 item 7 in spirit; prune after consumer check is PROPOSED and OPERATOR-GATED

## <review process>

F043 | INFERRED | Two sub-agents misbehaved: one wrote scratch scripts outside the tree (three files under E:/Windows/Temp named s04a*, left because the delete needed approval), another let an empty-stdin interpreter emit about 5 GB of output before it was killed. Disk and process checks afterwards were clean. Removing the three files (and the stray E:/Windows folder if empty) is operator-gated. | status: PROPOSED; OPERATOR-GATED

## Count table

Start snapshot: 2026-10-24T03:30:54, total 35931 files.
- git: 4205
- generated: 4476
- inbox: 877
- outbox: 45
- authored: 2407
- worktree: 19483
- nested-repo: 4435
- save: 3

Reviewed: 2407 authored rows (2323 from sub-agent row files, plus 42 driver rows for
account-id-named entries) plus 33524 files in aggregate and per-tree units.
Reviewed total: 35931. Snapshot total: 35931. Equal: YES.

Drift after the snapshot (reported separately, not mixed into either number): a second
walk at 2026-10-24T04:02:53 counted 33841 files, a difference of 2090. Three linked worktrees were pruned
by another session during the run, git objects shifted, one worktree grew slightly, and one
authored path appeared while one vanished. The authored count was 2407 on both walks.

Per top-level folder (files, snapshot): .git=4205, .mypy_cache=18, .pytest_cache=5, .ruff_cache=67, <channel inbox folder>=877, moon_sync_outbox=45, <root-files>=16, .claude=18896, .githooks=3, .github=9, certs=2, clockspeed=148, config=3, corpus=1, data=59, docs=55, memory=24, ops=498, scripts=8, shell=582, tests=706, tools=61, work=9643

Findings: 43. KNOWN 7, PROPOSED 25, NOT-APPLICABLE 11; OPERATOR-GATED 9.
