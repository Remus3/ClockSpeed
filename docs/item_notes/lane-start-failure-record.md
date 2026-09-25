<!-- Annex to the lane items CS-1017 and CS-1018 in ROADMAP.md, and to CS-1001.
A DECLARED DEPARTURE from the one-leaf-per-phase rule in docs/item_notes.md, recorded
in the leaf table there rather than made silently, on the precedent
docs/item_notes/cs988-sweep-record.md set. It is a read-only DIAGNOSIS of a live
operational failure for OPEN items, not an item body, and it is not archived because
docs/_archive/ is excluded from search and sections 6 and 7 are the direct input to
whoever next considers re-arming the lane. -->

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.
Filed 2026-09-13 in session 91.

# The lane start failure - a READ-ONLY diagnosis, filed 2026-09-13

SUBJECT: the failing lane cycles of 2026-09-11 and 2026-09-10. That date is the
INCIDENT's, not this section's - the diagnosis is live and the items it feeds are
open, so the date sits here rather than in the heading, where the closed idiom
vocabulary reads a leading date as marking a section historical.

Slice B, session 91. Base `9a7e152`. **No lane, driver, worker, `launch_queue_loop.ps1` or
`run_lane.ps1` was run. `ops/loop/control/lanes/QUEUE_STOP` was read and not written.**

**Revision note.** An earlier draft of this file rested its case on a duration argument.
That argument was refuted on a does-it-reproduce lens and every measurement below was
re-taken by hand against the live artifacts. The conclusion is unchanged; the argument for
it is different, and the refuted reasoning is recorded in section 4 so nobody rebuilds it.

---

## 1. Headline conclusion

**The runner did not fail to start. It started correctly and was KILLED by the launcher that
had just spawned it.** The 134-byte log is the signature of `taskkill /F` landing on the
PowerShell wrapper after the header was flushed and before the exit line could be written.

The root cause is a DOUBLE-IMPORTED `lanes` module giving the driver and the launcher two
separate ownership maps. This is CS-1000, closed 2026-09-13 - see its dated heading in `docs/LEDGER.md`,
commit `6d7ca37`. Cited by heading rather than by line, because line numbers into an
append-only file drift the moment anything is prepended above them. The mechanism trace in section 2 was re-derived here from the
blobs actually in force at the time of failure.

---

## 2. The primary argument - a mechanism trace, no timing required

This is the whole case. It needs no durations, and it predicts the one thing the artifacts
show most clearly: cycle 1 succeeds, every later cycle dies.

**The two module objects.** At the commits in force on 2026-09-11 at 13:02 - `dd182d7` for
the launcher, `e0523d8` for the driver - neither file publishes the dotted name:

- `ops/loop/lane_launcher.py`'s module-level `_LANES_MODULE_NAME` is
  `"clockspeed_loop_lanes"`, and its by-path load registers under that private name.
- `ops/loop/queue_loop.py`'s module-level module table maps `"lanes"` to the triple
  `("ops.loop.lanes", "cs_loop_lanes", "lanes.py")`, and its `_mod` fallback registers
  under `cs_loop_lanes`.

The detached driver is started by path, so `ops/loop` is on `sys.path` and the repository
root is not; `import ops.loop.lanes` fails for both files and each takes its own fallback.
Two module objects means two module-level `_OWNED` dicts, in ONE process - the launcher is
imported by the driver and runs inside it.

**Cycle 1 - the repoint succeeds by accident.** `_is_ours` (`ops/loop/lanes.py`'s `_is_ours`)
reads `_OWNED.get(path_key(lock))`; in the LAUNCHER's copy that is empty, because the
driver's `try_acquire_lane` wrote its entry into the OTHER copy. So the function falls
through to `return identity[2] == os.getpid()`. `identity[2]` is the record's `pid`, which
at that moment is the claiming driver's pid, and `os.getpid()` is the same process. True.
`repoint_lane_pid` rewrites `record["pid"] = worker` and sets the LAUNCHER's `_OWNED[key]`
to `(run_id, stamp, worker)`.

**Cycle 1 - the release refuses.** `_identity` (`ops/loop/lanes.py::_identity`) is `(run_id, ts, pid)`. The
driver's own `_OWNED[key]` still holds `(run_id, ts, driver_pid)` from the acquire, while
the on-disk record now reads `(run_id, ts, worker)`. `release_lane`'s `_is_ours` check, in
`ops/loop/lanes.py::release_lane`, compares them, they differ, and the release is refused. The lane is never freed.

**Cycle 2 onward - the kill.** The next acquire finds the lock held by a dead worker,
reclaims it, and rewrites the record with a fresh `run_id`, `ts` and pid, updating the
DRIVER's map. The LAUNCHER's map still holds cycle 1's stale triple, so this time `owned is
not None` and `_is_ours` takes `identity == owned`, which is False. `repoint_lane_pid`
returns False at `ops/loop/lanes.py`'s `repoint_lane_pid`, and `ops/loop/lane_launcher.py`'s `launch_lane`, at its `_kill` call
runs `_kill(pid)` on the worker it spawned three lines earlier.

**What the trace predicts, and what the rows show.** Cycle 1 completes; every subsequent
cycle is killed. `ops/loop/reports/queue_loop.jsonl` holds exactly that shape twice - 09-10
and 09-11 - and it is the shape a dirty tree, a missing tool or a bad prompt do not produce,
because none of those would let cycle 1 through.

**Why the log is exactly the header.** `ops/loop/run_lane.ps1:57-58` writes the header with
`Out-File -Encoding utf8`, which emits a BOM under Windows PowerShell 5.1: 3-byte BOM + 129
characters + CRLF = 134. Line 72 merges every stream into the pipeline with `*>&1` and line
73 appends it to the same file, so anything the runner or the worker emitted would have
GROWN the file. There is no `trap`, no `try/finally` and no exit handler anywhere in the
file - the exit line at 75-76 is an ordinary statement. A file that is exactly the header
therefore means the process emitted nothing and was terminated externally.

**Corroborating, weakly:** `ops/loop/control/lanes/` has directory mtime 2026-09-11
13:02:48, i.e. the lock directory was last written during that run. It shows lock churn in
the right window and nothing more.

---

## 3. The 09-10 / 09-11 split, stated because pooling hid it

Twelve `launch_failed` rows exist in `ops/loop/reports/queue_loop.jsonl`. They are NOT one
population:

- **Eleven are 2026-09-10**, 23:17 to 23:29.
- **Exactly ONE is 2026-09-11**: run id `5ff0ddfd`, 13:02:03, duration 2.091s.

`5ff0ddfd` is the row this document is named after, and it is the weakest member of the pool
on every measure taken below - the shortest duration and the smallest header offset. Any
claim asserted over the pooled twelve is met by its strongest members while this one goes
unmeasured. That is the pooled-guard shape this project already has on record, and the
earlier draft walked straight into it.

---

## 4. REFUTED - the duration argument, recorded so it is not rebuilt

The earlier draft argued: `_SPAWN_LIVENESS_GRACE_S = 2.0`, every failed row ran 2.09 to
3.15s, a genuine `runner_exited_early` would be under 2.0s, therefore early exit is
excluded. **That argument is wrong three times over and must not be reinstated.**

**It compares two different clocks.** `duration_s` is the DRIVER CYCLE wall clock:
`ops/loop/queue_loop.py`'s `run_cycle` sets `started_at = clock()` before the acquire loop begins,
and the same function writes `round(ended_at - started_at, 3)` (as of `9a7e152`). The 2.0s
grace is `proc.wait(timeout=_SPAWN_LIVENESS_GRACE_S)` at `ops/loop/lane_launcher.py`'s `_spawn`, at its `proc.wait` on the grace,
measured from the `subprocess.Popen` in `ops/loop/lane_launcher.py::_spawn`. A row is `pre_spawn + t_exit + release`, so
a runner exiting at 1.97s produces a row above 2.0s. The inference does not follow.

**Bounded independently, it excludes almost nothing.** The worker log's mtime minus the
cycle's `started_at` is an upper bound on `pre_spawn` (the header is written after the
spawn, and the file was never appended to). Measured offsets run 0.116s to 2.210s. An early
exit is excluded only when `duration - offset >= 2.0 + post_allowance`:

| post-spawn allowance | rows excluding an early exit |
|---|---|
| 0.00s | 4 of the 11 logged rows, margins +0.020 to +0.321 |
| 0.05s | 1 of 11 |
| 0.35s | 0 of 11 |

**And it never excluded the 09-11 row at all.** `5ff0ddfd`: duration 2.091, offset 0.116,
room 1.975 - short of 2.0 even at zero allowance, margin **-0.025s**. The one row this
document is about was never covered by the argument that was supposed to settle it.

**It was not independent of the prior it claimed to escape.** The earlier draft correctly
warned that agreeing with the CS-1000 ledger entry is not evidence, then nominated the
durations as the thing standing outside that shared prior. `docs/LEDGER.md:107` already
reads "EVERY subsequent cycle failed in 2.1 to 3.2 s". The arithmetic was inside the prior
the whole time.

---

## 5. Hypotheses discriminated

| Hypothesis | Verdict | What settled it |
|---|---|---|
| Dirty lane worktree refused the launch | REFUTED | No code reads worktree state. `ensure_worktree` returns early once `.git` is present and runs no git on a reused tree. `docs/LEDGER.md:1385-1392` records CS-970 refusing to add such a check on purpose - a dirty lane tree is normal between cycles. |
| `QUEUE_STOP` stopped the runner | REFUTED | The token appears in neither `run_lane.ps1` nor `lane_launcher.py`. It is read only by `launch_queue_loop.ps1:105-119` (pre-spawn, `exit 2`) and by the driver between cycles. Either path yields NO log, not a 134-byte one. |
| `claude` missing or unresolvable | REFUTED | `Get-Command claude -ErrorAction Stop` is at `ops/loop/run_lane.ps1:37`, before the header write at 57. Failure there yields a zero-byte log. |
| Prompt file missing or unreadable | REFUTED | `Get-Content` at line 71 is after the header, and `*>&1` would put its error into the log, growing it past 134. |
| Model config drift | REFUTED | `ops/loop/config.json` does not exist and is gitignored, so the line-46 fallback is taken every fire. Every log reads `model=claude-opus-5`. |
| A startup-path regression landed in the window | REFUTED | The five commits touching `ops/loop/` between 09-09 and 09-12 are all CS-970 and all land 14:32 or later, after the last failing cycle at 13:02. `run_lane.ps1` has one commit in its whole history (`e0523d8`, 09-06). The path was byte-identical on the 09-10 night, which failed the same way. |
| CS-1012 is related | REFUTED | CS-1012 is the CI runner's tier-1 duration gate. "Runner-side" there means the GitHub runner, not `run_lane.ps1`. A false lead on the word alone. |
| `runner_exited_early` | NOT EXCLUDED by timing, but unnecessary | See section 4. The mechanism trace explains every row without it, and no artifact supports it. |
| **A stale or corrupt lock, as an ALTERNATIVE cause** | REFUTED as an alternative | It is a CONSEQUENCE, not a rival. With a single `lanes` module the trace gives reclaim followed by a SUCCESSFUL repoint, so a stale lock alone cannot produce a refusal. It is what the double import leaves behind. |
| **Pid reuse** | REFUTED | `_is_ours` (`ops/loop/lanes.py`'s `_is_ours`) never consults liveness - it compares an identity triple, or falls back to `os.getpid()`. No pid-reuse condition can flip it. |
| Double-imported `lanes`, launcher kills its own worker | SUPPORTED | Section 2. The only path in the tree producing this log shape, and the only one that predicts cycle-1-succeeds. |

---

## 6. Still open

1. **A permissions or IO fault on the lock write.** `ops/loop/lanes.py`'s `repoint_lane_pid`, at its `_atomic_write` returns False
   when `_atomic_write` fails, which reaches the same `_kill`. Genuinely open, weakly
   disfavoured: `try_acquire_lane` successfully wrote a fresh lock on all twelve cycles, so
   the directory was writable each time.
2. **Whether the CS-1000 fix works against a real spawn.** `docs/LEDGER.md:117-118` records
   it as UNVERIFIED - the arm fakes the spawn seam. CS-1001 is filed on the residual: the
   fix rests on there being exactly ONE `lanes` module object in a process, and nothing
   asserts it.
3. **Whether anything ELSE also breaks cycle 2.** The kill explains the log shape
   completely, so a second independent fault would sit invisible behind it. One sufficient
   cause is not proof of a single cause.
4. **Cycle 8's gap.** Run id `62f29b90`, 2026-09-10 23:25:52, duration 3.151s - the LONGEST
   row - and the only failed cycle with no log file at all. The gap from cycle 7's start to
   its own is **262.5s**, against 47.9 to 70.4s for every other gap in the file. Its absent
   log does NOT place it before the spawn: `_log_path` (`lane_launcher.py`'s `_log_path`) creates
   only the DIRECTORY and returns a path, and the runner creates the file - so
   "no log" is consistent with a spawn that never got as far as the header. Being the
   slowest row where a pre-spawn failure would be the fastest, it fits the kill model
   rather than contradicting it, but the 262.5s gap is unexplained.

---

## 7. What would actually settle it

Neither of these is available today, which is precisely why a duration argument had to be
invented in the first place.

1. **Run CS-1001's acceptance, read-only.** It is the arm that asserts one `lanes` module
   object per process - the exact predicate the whole diagnosis and the whole fix rest on.
2. **Make the row self-describing.** Have the launcher record (a) the seconds `proc.wait`
   actually consumed and (b) the refusal reason, into the cycle record. Today the row
   carries neither: `detail` on all twelve rows is the bare string `LaneLaunchError`,
   because the reason words landed in `aa5a828` at 14:32, ninety minutes after the last
   failing row. With those two fields, `runner_exited_early` and `repoint_refused` are
   distinguishable by reading one line, and no timing reconstruction is needed at all.

---

## 8. What agreement here is worth

This reconstruction and the repository's CS-1000 entry agree, and **that agreement is still
not evidence** - both read the same eleven logs, the same JSONL and the same tree. What the
rewrite changes is that the load-bearing argument is now a code trace over cited lines,
which a reader can check against the blobs rather than against a shared prior. The earlier
draft's nominated independent measurement turned out to be quoted in the ledger it was
meant to be independent of.

## 9. Note on the QUEUE_STOP text

`ops/loop/control/lanes/QUEUE_STOP` (1540 bytes, mtime 2026-09-11 17:33:06) records the
operator's expectation:

> "Expect runner_exited_early or spawn_failed - the proximate mechanism, pointing at the
> runner rather than at whatever actually refused."

The trace says the row will read neither: it will read `repoint_refused`. The sentinel's own
second clause names the trap exactly - the runner here is the victim, not the fault. The
file was read only and left as found.
