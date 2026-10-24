# CS-1295 repo review plan (session 151)

Section status: HISTORICAL. Review-only plan for CS-1295, written by the headless
session 151 run on branch review/cs1295-s151, cut at main 726acf1f. Scope: count every
file under the main checkout from a start snapshot; review authored files one by one and
each generated or worktree tree as one row; fix nothing, delete nothing, take no new id.

## Snapshot

Snapshot time: 2026-10-24T03:30:54. Total files: 35931.
Earlier walks gave 38960 and 38171: the live tree lost linked worktrees between walks and
five unmarked duplicate repo copies under work/ were reclassified from authored to single-row
units. The third walk, taken before any review, is the start snapshot used throughout.

Per class: git=4205, generated=4476, inbox=877, outbox=45, authored=2407, worktree=19483, nested-repo=4435, save=3
Authored by git state: tracked=620, ignored=1787

Per top-level folder (files): .git=4205, .mypy_cache=18, .pytest_cache=5, .ruff_cache=67, <channel inbox folder>=877, moon_sync_outbox=45, <root-files>=16, .claude=18896, .githooks=3, .github=9, certs=2, clockspeed=148, config=3, corpus=1, data=59, docs=55, memory=24, ops=498, scripts=8, shell=582, tests=706, tools=61, work=9643

## Units (non-authored)

- git: 4205
- generated:.mypy_cache: 18
- generated:.pytest_cache: 5
- generated:.ruff_cache: 67
- inbox: 877
- outbox: 45
- worktree:.claude/worktrees/agent-a0e0b461487f82a18: 724
- worktree:.claude/worktrees/agent-a11badacdf15b8cb4: 1126
- worktree:.claude/worktrees/agent-a19a1101efff97773: 665
- worktree:.claude/worktrees/agent-a1b08f9553779e024: 782
- worktree:.claude/worktrees/agent-a1ca6574c0fe3231a: 744
- worktree:.claude/worktrees/agent-a2b6051f5e76ede83: 465
- worktree:.claude/worktrees/an account-id-named entry #2: 782
- worktree:.claude/worktrees/agent-a301eedf9a4d13fae: 694
- worktree:.claude/worktrees/agent-a3040e24c9008c13d: 798
- worktree:.claude/worktrees/agent-a4680c300742bd2e8: 1133
- worktree:.claude/worktrees/agent-a47d3ed3ae73c739f: 1107
- worktree:.claude/worktrees/agent-a50232a210328da57: 537
- worktree:.claude/worktrees/agent-a50e3824837d24fcd: 753
- worktree:.claude/worktrees/agent-a696864ecd64dbe42: 768
- worktree:.claude/worktrees/agent-a8915505dc0a69d68: 736
- worktree:.claude/worktrees/agent-a8d21d7d20ea1b118: 1140
- worktree:.claude/worktrees/an account-id-named entry #3: 995
- worktree:.claude/worktrees/an account-id-named entry #4: 658
- worktree:.claude/worktrees/agent-ada15e8ddd25abf3f: 805
- worktree:.claude/worktrees/agent-ae6825afcde250bcc: 1133
- worktree:.claude/worktrees/agent-ae6cedd3443ae97ae: 523
- worktree:.claude/worktrees/agent-aeb066f9abbf062c9: 691
- worktree:.claude/worktrees/agent-afb8ac949de968d20: 1116
- generated:shell/node_modules: 562
- generated:work/.ruff_cache: 3
- nested-repo:work/s136_b1_clone: 629
- worktree:work/s137_cs1308f2_land_wt: 608
- nested-repo:work/s137_cs1308f3_land_wt: 658
- nested-repo:work/s137_cs1308f3_old_wt: 626
- generated:work/s137_cs1309f1_base (duplicate repo copy): 661
- generated:work/s137_cs1309f1_cand (duplicate repo copy): 665
- generated:work/s137_cs1309f1_mut (duplicate repo copy): 656
- nested-repo:work/s137_cs1309f2_base: 1262
- nested-repo:work/s137_cs1309f2_mut: 1260
- generated:work/s137_cs1309f3_base (duplicate repo copy): 658
- generated:work/s137_cs1309f3_mut (duplicate repo copy): 656
- generated:__pycache__@clockspeed (11 dirs): 69
- generated:__pycache__@ops (3 dirs): 25
- generated:__pycache__@scripts (1 dirs): 4
- generated:__pycache__@tests (11 dirs): 391
- generated:__pycache__@tools (1 dirs): 25
- generated:__pycache__@work (4 dirs): 11
- save:corpus (aggregate): 1
- save:work (aggregate): 2

## Slices

Order: smallest authoritative folders first, then tests, ops/loop, work last.

- S01 root files, .claude, .githooks, .github, certs, config, corpus (aggregate), root scratch
- S02 clockspeed, scripts, shell, docs, memory, data
- S03 tools, ops (non-loop)
- S04a/S04b tests (two halves by sorted path)
- S05a/S05b ops/loop (two halves; runtime state files, content only skimmed)
- S06a..S06e work scratch (about 250 per slice, sorted path)

## Review topics

Hierarchy; memory recall (memory/, hand-off, WAKEUP_NOTES); dated files for archive
(list only, with consumer check); pins, leaves, worktrees, scratch, orphans, stale;
outside-the-repo references (candidates for <sidecars>/CS); the .md set and the
CLAUDE.md section 4 owner table; inferred topics marked INFERRED.

## Known findings folded in

docs/item_notes/phase7.md sections CS-1291, CS-1292, CS-1293; every existing BACKLOG.md
line; docs/_scratch/cs_worktree_classification.md. Overlaps are marked KNOWN.

## Method

Foreground sub-agents, at most three at once, write rows to data/repo_review_s151/rows/;
the path list stays in data/ and is never committed. Closing check: rows equal snapshot.
