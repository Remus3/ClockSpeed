# Wakeup notes

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**The last two to three sessions at full fidelity, newest first. Nothing older.** When a
fourth session lands, the oldest entry is moved to `docs/history_notes.md` - relocated,
never deleted.

This file is read at session start, alongside `CLAUDE.md`, the memory index, `ROADMAP.md`
and `docs/ARCHITECTURE.md`. It is refreshed by the `/done` ritual at the end of every
session, not written incrementally during one.

It holds what a fresh session cannot recover from the code and the git log: what was
actually in flight, what was tried and abandoned, and what the very next action is. It
does not hold per-item completion records - those are ledger entries and belong in
`docs/LEDGER.md`.

## Entry format

```
## Session <n> - <YYYY-MM-DD> - <one-line focus>

- Shipped: item IDs closed this session. Detail in docs/LEDGER.md, not here.
- In flight: what was left mid-work, where it stands, and what it is blocked behind.
- Decisions: ADRs recorded this session, by id. Detail in docs/adr/.
- Surprises: anything that contradicted a spec, and which file was updated as a result.
- Failed paths: what was tried and abandoned, and why - so it is not retried next session.
- Next action: the single first thing the next session does.
```

Keep every entry to that shape. If an item needs a paragraph, it needs its own file and
the line becomes a pointer.

---

## Session 65 - 2026-09-06 - THE CLOSURE WAS REFUTED 3/3 AND THE MECHANISM FELL TO ONE LINE; four routes repaired, nine mutations now killed, and one of my own arms scored its own mutation green

- **Shipped:** nothing CLOSED. One commit, `77a88d1`, on top of `58a30f1`. Detail in
  `docs/LEDGER.md`, not here.
- **In flight:** CS-896 stays OPEN; CS-917's acceptance was TIGHTENED and needs an
  operator eye; the ROADMAP relocate pass is still owed.
- **Decisions:** no ADR. Two questions are put to the operator and neither was decided
  by an agent - see below.
- **Surprises:** the four routes below, all measured against a tree every gate was green
  over.
- **Failed paths:** closing CS-896 by transferring its residual to CS-917. REFUTED, and
  the reasoning is in the ledger so it is not retried.
- **Next action:** put the two operator questions below. CI on `77a88d1` is ALREADY
  READ and was GREEN - reading six is filed in the CS-896 leaf, and it is the worst
  fast reading yet by one second, leaving 60s of margin against a 100s spread.

**CI RUN 34038527058 ON `58a30f1` WAS GREEN** - that was the previous session's open
question and it is answered. Five consecutive green sharded runs. The fifth reading:
fast 353 job-seconds, save 247; the lane's own lines read 346 and 240 within budget.

**THE CLOSURE WAS PROPOSED, FROZEN AT `58a30f1`, AND REFUTED BY THREE ADVERSARIES on
distinct lenses - measurement integrity, scope laundering, guard defeat.** Every
load-bearing citation was then verified by the merger against `git show 58a30f1:` rather
than the working tree, **because one adversary was mutating that tree while the other two
read it.** That was an orchestration error on the merger's part; the md5 of the workflow
was recorded BEFORE dispatch and matched afterwards, so the readings stood. **Do not
dispatch a mutating adversary alongside readers of the same file again.**

**THE MECHANISM CS-896 BUILT WAS DEFEATABLE IN ONE LINE, FOUR WAYS.** Each left guard (k)
printing PASS, its own detail asserting the levels were "pinned two-way", and the budget
module green:

1. a job-level or step-level `env:` block restating either level - the guard anchored at
   line start, so a FLOW mapping never begins one and was invisible while PyYAML resolved
   it. The BLOCK spelling WAS caught. **The third regex-versus-parser hole in this guard
   in three sessions.**
2. `continue-on-error` on a job or step, discarding the ceiling's exit. **Governed by
   nothing** - the key appeared nowhere under `tests/` or `tools/`.
3. a second key written into `$GITHUB_ENV` from the start step.
4. the report step reading a level it cannot parse - all three refusals guarded the start
   marker and neither level had one, so a run far past every level printed the healthiest
   verdict it has and exited 0.

**ALL FOUR REPAIRED, NINE MUTATIONS THAT WERE GREEN NOW REDDEN** - five against the guard
record, four against the arms. Module 122 -> 141 passed. Both shards green locally: fast
3949 passed, save 1413 passed.

**ONE OF MY OWN ARMS SCORED ITS OWN MUTATION GREEN.** The first `$GITHUB_ENV` arm matched
greedily; a plain YAML scalar FOLDS a continuation line into the same string, so the
greedy run reached past the smuggled write to the last marker and captured one key where
there were two. **It reported the property held with the mutation in the tree.** Only the
mutation proof caught it. An arm that passes on a clean tree has proved nothing until its
mutation is shown to red it.

**GUARD (k) ALSO CAUGHT ME**, correctly: the first draft of these arms quoted the override
in its docstrings, making the test module a second owner of the numbers. Plants are now
ASSEMBLED at call time, the convention `restatement()` already documents.

**THE BROADER SUITE CAUGHT A THIRD THING THE TARGETED RUN DID NOT** -
`tests/test_exception_rendering.py` found my new guard code rendering a caught exception
OBJECT into a message, which is non-negotiable 12. Repaired with `_exc_text`. **Run the
shard, not just the module.**

**A CLAIM I MADE AND RETRACTED.** I proposed the runner swing is SHARD-SPECIFIC (save
shard 16s step spread against the fast shard's 94 over the same five runs). An adversary
refuted it and I verified: the shards are INDEPENDENT DRAWS, so under a pool with a fast
class appearing once in five fast-shard draws, the save shard missing it in five has
probability 0.8^5, about one in three. An identical pool reproduces the contrast exactly.

**THE DISPOSITION OF CS-896 TURNS ON ONE OBSERVATION.** Drop the single low fast reading
and that shard's spread falls from 94s to 34s, and the shipped band is then WIDER than the
noise - the condition PASSES. Keep it and it FAILS. `n=5` cannot say which, which is
exactly why another reading is the wrong instrument.

**THE FEASIBILITY ARITHMETIC, NEW AND RECORDED IN THE CS-896 LEAF.** With `M` the worst
reading and `N` the spread: no false warn needs `B >= M`, a warn before a red needs
`C - B >= N`, a red rather than a cancel needs `C + N <= cutoff`. So `B <= cutoff - 2N`,
the feasible budget window is `[M, cutoff - 2N]`, EMPTY once `N > (cutoff - M) / 2`. The
window is currently non-empty and the SHIPPED budget sits outside it. **THE LEVELS WERE
NOT TOUCHED and must not be re-derived at this sample size** - three previous
re-derivations were each falsified by their own next reading. A distribution-free 95/95
bound needs `n >= 59`.

**TWO QUESTIONS FOR THE OPERATOR, NEITHER DECIDED BY AN AGENT.**
1. **CS-917's acceptance was TIGHTENED** to require the band not be narrower than the
   noise figure it is derived from. Two adversaries found it could otherwise close with
   the condition silently dropped. It is a tightening, not a narrowing, but moving an
   acceptance clause is not an agent's call - review it.
2. **Whether CS-896 closes as an HONEST PARTIAL.** Precedent is in `docs/LEDGER.md` under
   CS-421 and CS-882, both operator rulings. No adjudicator can grant it and none was
   asked.

**NAMED AND NOT CLOSED.** ROADMAP.md is at 70987 bytes against a 61440 budget (115 per
cent) and this session added two bytes to it. THE RELOCATE PASS IS STILL OWED, three
sessions running. RELOCATE, NEVER DELETE.

**THE ECC FOLLOW-UPS ARE STILL UNFILED, and one count in the handoff was already stale:**
the GitHub Actions carry **13** mutable `uses:` tags, not 11 - the shard split added two.
A restated count drifted inside one session, which is the doc rule demonstrating itself.

---

## Session 64 - 2026-09-06 - CI was red for TWO reasons and the handoff named one; tier 1 now runs in two shards; FOUR adversarial passes all returned REFUTED and CS-896 is STILL NOT CLOSED

**ZERO ITEMS CLOSED.** CS-910, CS-900 and CS-896 all took substantive repairs and all three
stay open. Seven commits, `8729191..b9ca505`, all pushed, CI green.

**THE HANDOFF WAS WRONG ON ITS TOP ITEM.** It said tier 1 was red on the duration ceiling
alone with every test passing. Both red runs read `1 failed, 5213 passed, 119 skipped`. The
lane was red for TWO reasons and only one had been read.

**CS-910 - a Windows-only arm ran on Linux.**
`tests/test_make_cert.py::test_a_planted_openssl_in_the_working_directory_is_never_run`
grades the implicit current-directory executable search. Two of the three CS-910 runtime
arms carry a platform skip; the third carried a LIVENESS GATE written
`os.name != 'nt' or NeedCurrentDirectoryForExePath(...)`, which SHORT-CIRCUITS TRUE on
POSIX - so it reported the mechanism live where it does not exist. Fixed with the skip its
siblings had, plus a structural guard that reads every test function's UNPARSED BODY for the
two spellings, because the offending arm named the module only inside a probe STRING.

**WHY IT ESCAPED, AND THE FIRST FILED CAUSE WAS WRONG.** Not `cancel-in-progress`. **GitHub
Actions creates one run per PUSH event, against the TIP commit.** Twelve commits went up in
one push; the commit that introduced the test was never eligible for a run. The development
machine is Windows, where the arm passes, so tier 0 could not see it either.

**CS-900 - the liveness sweep re-parsed 8.4 MB of source 3457 times.** `module_function` took
a module's SOURCE and called `ast.parse` on it for every question. **89.93s before, 0.89s
after**; twelve sibling helpers in the same module had the identical shape and now share one
cache. `tests/test_liveness.py` went from roughly 146s to 41.19s.

**TIER 1 NOW RUNS IN TWO SHARDS, and that was an operator decision.** Run 34013336391 was
CANCELLED at 611s at 99 per cent of the suite with NOTHING FAILING. The cutoff is policy and
was not raised, so the work was given a second runner rather than trimmed: `fast` runs
`tests --ignore=tests/save`, `save` runs `tests/save`. **Coverage is unchanged BY
CONSTRUCTION** - verified two ways, a node-id partition (3245 + 1413 = 4658, empty
intersection) and identical skip sets (49 sites, 120 skips) before and after.

**FOUR ADVERSARIAL PASSES, ALL FOUR REFUTED, each against a frozen SHA it had not written.**
Every one found a defect that every gate, guard and arm in the tree was green over:

1. The budget's derivation was falsified BY THE SPLIT ITSELF - 540 was "21 above the worst
   observed job" and the split left it 221 above, so **CS-896's fix had disabled CS-896's
   own alarm**.
2. **The partition guard read ONE SIDE.** Adding one ignore and one marker expression to the
   save shard dropped **244 of its 1413 tests** with everything green.
3. **A trailing YAML comment defeated the cutoff guard.** `  third:  # a scratch job` was
   invisible to a regex anchored at `:$` while PyYAML resolved three jobs - that job would
   have run under GitHub's 360-minute default.
4. The warning margin was overstated 2.5x, and a ledger entry cited evidence THIS SESSION'S
   OWN COMMIT had deleted.

**AND A FIFTH FINDING CAME FROM THE DATA.** Reading four of the fast shard arrived at **260
job-seconds** against 323, 359 and 358 - on a **byte-identical population** (`3911 passed, 23
skipped` in both runs), an **88-second swing on identical work**. That widened the sample sd
from 20.5 to 46.5 and pushed the 95/95 tolerance bound to **564s, above the 480 ceiling**.
**The fourth reading did not discharge the sample objection - it failed it.**

**SO CS-896 IS NOT CLOSED, and the reason is specific.** The ROADMAP acceptance clause is met
four times over. What is NOT met is the CS-896 leaf's added condition that growth be visible
before it is fatal, because every warn band this session derived was narrower than the noise
its own next reading revealed: 21s, then 36s, now at least 88s.

**LEVELS SHIPPED AT 420 / 480 AND ARE NOT THE COMPLAINT.** All four readings sit inside them;
the worst fast reading is 359 and the worst save reading 237. A fifth re-derivation on n=4
would repeat the mistake the last three made.

**CS-917 FILED** - the growth SLOPE (3.51s per commit) is owned by no item, verified at three
SHAs.

**THE ECC TRIAGE: TAKE NOTHING.** `https://github.com/affaan-m/ECC`, MIT, verified 250044
stars. The licence gate CLEARS, so the refusal is on quality: our character-set gate bans
every byte above 0x7E while ECC's allowlists (c), (R), (TM) and does not ban an em-dash;
our PII layer resolves account ids and world tokens at runtime against its two regexes.
**ECC fails our non-negotiable 4 itself**, and its installer writes `~/.claude/` by default -
running it would modify our FROZEN `.claude/settings.json` with no grant. IDEAS-ONLY.

---

## Session 63 - 2026-09-05 - CS-911 and CS-912 CLOSED; the HUD style layer took SEVEN audit rounds and none returned CLEAR; CS-910's done-claim was REFUTED TWICE and three of four adversaries returned REFUTED

**CLOSED.** CS-911 - every stage takes a unique filename and opens `"wx"`, so the
truncation primitive is gone rather than made unlikely. CS-912 - `/api/registry` publishes
the registry as a tenth route, and 731 of 731 producible items built a solve request naming
only published identifiers.

**OPEN, and both for reasons worth reading.** CS-910 routed seven spawn sites and its commit
message claimed the remainder was all frozen. That was FALSE TWICE: `scripts/verify_env.py`
is not frozen, was on the write-list, and still put a bare `git` into three argv; and the
remainder is FIVE indirect delegations, not three. CS-913's filed cause is REFUTED by the
code and its line is rewritten.

**FILED.** CS-914 (the CS-911 shape in Python, on the DEFAULT production path), CS-915 (two
latent guard holes), CS-916 (one asset-extraction prerequisite that three separate features
are all gated on), CS-G06 (the mature-world corpus, an operator action).

**SEVEN CS-600 AUDIT ROUNDS ON ONE STYLE LAYER AND NOT ONE RETURNED CLEAR.** Rounds 1 to 4
each found the same fault one selector further out - the rule's own `color`, then its
`border`, then the nested `.hud-*` descendants, then every OTHER descendant - because every
repair defined its boundary as "the tokens something I can see reads". Round 4 named it:
each repair closed the set the previous auditor named and drew the new boundary exactly
where the previous finding stopped. WHAT ENDED IT WAS A MEASUREMENT, NOT A BETTER REPAIR:
the four `--overlay-*` tokens were byte-identical to the DARK values of `--bg`, `--text`,
`--accent-hud` and `--hud-rule`, so the overlay palette had been the dark palette all along.
Rounds 5 to 7 then left the palette entirely - `color-scheme` is not a custom property;
round 6 found the round-5 fix had landed on `.hud-overlay`, which renders ZERO times, while
`:root` had none; round 7 defeated the repaired guard with an OPTIONAL TRAILING SEMICOLON.
Round 7 graded the RENDERED page PASS on all five phases with zero live defects, and THE
OPERATOR RULED TO COMMIT on that evidence. Every finding is repaired and each is proven by
a planted mutation.

**THE MEASUREMENTS WORTH KEEPING.** #FA9549 scores 2.22 / 2.07 / 1.96 on this page's own
LIGHT grounds - it fails even the large-text threshold there, not merely over a game pixel,
because a light theme IS a white pixel that is always on screen. Contrast over a scrim is
NOT MONOTONIC: it falls from 2.22 at no scrim to 1.02 near alpha 0.35, where the composited
ground crosses the accent's own luminance, then climbs to 8.38 opaque. A light scrim lands
at the WORST legibility available.

**THREE OF FOUR ADVERSARIES RETURNED REFUTED, WITH DISTINCT LENSES.** Security found three
live bare-name spawns in a non-frozen file plus both guards blind to them. Does-it-reproduce
found CS-912's paired control vacuous - it SUBSTITUTED the foreign key into a request naming
one recipe, so it also removed the target's own producer, and proved it with a live mutant
that kept the arm green while `tests/solve` went red. Completeness found four guards each
reporting zero findings because they could not SEE findings. Scope confirmed the
`workdir.py` race is reachable on the default path and measured 31 of 240 concurrent copies
failing. FOUR LENSES, FOUR DIFFERENT CLASSES - repeated skeptics would have found one.

**OPERATOR RULINGS THIS SESSION.** Commit on audit round 7 rather than iterate to CLEAR.
Wiki and community sources are READ-AND-CITE ONLY - CS-485 stands, no dataset is lifted, no
crawl is run. The local `Satisfactory Designs` downloads are REVIEW ONLY and nothing derived
from them is committed.

**A UI/UX DOCTRINE FROM ANOTHER PROJECT WAS INGESTED** and adapted into
`docs/hud_doctrine.md`, which is now the owner file for the two surfaces. It records what
does NOT transfer as carefully as what does, and names THREE SHIPPED ARMS an overlay will
collide with: the no-timer arm, the one-clickable-target arm, and the 7-bit ASCII arm, which
with a CSP publishing no `img-src` leaves an overlay with neither a glyph nor an image.

**TRAPS MEASURED THIS SESSION.** `dict(os.environ)` UPPER-CASES KEYS ON WINDOWS, so popping
a mixed-case variable removes nothing and the probe reports clean while measuring nothing -
it produced a GREEN result on genuinely defective code. A `;` CHAIN ENDING IN `tail` EATS
PYTEST'S EXIT CODE exactly as a pipe does: a red suite was reported as exit 0 twice, once to
me and once to a slice. AND I BROKE A FREEZE I DECLARED THREE TIMES - three separate agents
caught it independently; one recovered the start bytes and diffed to prove its verdict still
stood.

**NAMED AND NOT CLOSED.** ROADMAP.md is at 112 PER CENT of its soft budget and this session
made it worse; a relocate pass is owed. The HUD layer renders ZERO times today - it is a
published vocabulary waiting on `/api/plan` and `/api/advice`. Two design questions are open
and recorded in `docs/hud_doctrine.md`: whether the overlay keeps the companion's warm accent
when the game's own world is warm, and whether item identity and production status can share
the colour channel.
