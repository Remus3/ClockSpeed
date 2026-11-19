# Clockspeed - live per-item detail, phase 4 - save reader, CS-4nn

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**This is a leaf of `docs/item_notes.md`**, which owns the index and the rules this
file obeys. Read the index for the leaf membership rule routing every OPEN item, the verbatim
rule, and what this family never contains. Do not restate any of it here.

**What lands in THIS leaf.** Every OPEN item ROADMAP.md files under its `Phase 4` heading whose ID is
outside the `CS-8nn` block. `CS-501` is here because it predates that block
and ROADMAP.md files it under phase 4.

**Bodies are relocated VERBATIM.** Every section below arrived from
`docs/item_notes.md` unedited when that file was split on 2026-08-25, and arrived
there from `ROADMAP.md` and `docs/history_notes.md` before that. A body therefore
still reads as it did when it was written, including the parts a later session
measured false and corrected in place rather than rewriting.

**When an item CLOSES its section moves to `docs/history_notes.md`**, not to another
leaf. That move is what keeps this file live.

---

## CS-426

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-15 by the CS-420 adjudicator as the item it would take next, and independently confirmed by the control-validity adversary. FULL ENTRY relocated to this file under **CS-426 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: filed 2026-08-15 by the CS-420 adjudicator as the item it would take next, and independently confirmed by the control-validity adversary. **EVERY DISCRIMINATING TEST CS-420 SHIPPED IS LIBRARY-BACKED AND SKIPS WITH NO GAME INSTALLED.** Measured: with the new modules removed, the entire pre-existing suite exits 0 under `SetProperty 1 to 0` - it is blind to it - and `MapProperty 2 to 1` is caught by exactly one test, `tests/save/test_properties.py::test_every_measured_type_the_library_exercises_yields_at_least_one_value`, which is itself library-backed and therefore also skips on CI. So on a clone with no game, BOTH widths are unguarded. The one width evidence that runs everywhere is `test_both_tag_grammar_transcriptions_agree`, which compares the two TRANSCRIPTIONS and is blind by construction to a fault they share. **This is the CI half of the common-mode question and it is genuinely open**, unlike the real-library half, which session 8 measured to be already guarded - see the corrected note in `WAKEUP_NOTES.md`. Do NOT close this by asserting the fixture round-trips through our own loader: session 6 measured that a round trip cannot distinguish "matches the game" from "matches our reader", and a fixture packed with the same belief the reader unpacks with agrees by construction. **AMENDED 2026-08-16 (session 9): the scope GREW.** CS-420 shipped test_every_tag_width_is_caught_by_a_library_backed_oracle, which derives the whole width-to-detector relation and is ALSO library-backed, so it skips on a clone too. The CI gap is now the width discriminators AND the artifact that grades them. Note also the defect CS-420 found and fixed while here: those tests gated their skip on the SAVE library while the usmap comes from the INSTALL, so on a machine with saves and no install they FAILED rather than skipped - check any fixture built for this item against that configuration, not just against a bare box.

### Acceptance

a hand-authored payload exercising SetProperty and MapProperty tags turns red under `SetProperty 1 to 0` and `MapProperty 2 to 1` in an environment with no install and no save library, proven by running the save suite with discovery forced empty


## CS-432

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-420 builder as a stated residual of its own work, which is the correct place for it. FULL ENTRY relocated to this file under **CS-432 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-420 builder as a stated residual of its own work, which is the correct place for it. TWO SEPARATE PROBLEMS SHARING A FILE. FIRST, `_JOIN_WORD_FLOOR = 13` sits exactly at the pristine observed distinct-word count, and the join oracle's own liveness assertion still reads it. If this operator's world ever spans enough joined type words that no single-width mutant falls below 13, that assertion goes RED ON A CORRECT GRAMMAR. It is a FALSE RED and loud rather than a false green, which is why it ships rather than blocks, and the attribution test already avoids it by comparing against a pristine baseline measured in the same run - a single sweep has no baseline to compare against, which is why the fix is not simply copying that. SECOND, and structural: the cross-section oracle detects 0 of 6 widths, so `test_every_tag_width_is_caught_by_a_library_backed_oracle` cannot protect it - an oracle that detects nothing is indistinguishable from one gutted to a green no-op, and gutting it was measured to leave the suite passing. Its guard has to come from the fault class it IS sensitive to, the value-start rotation, not from the width attribution. **SHARPENED 2026-08-16 by the final audit, and it is worse than filed: the FLOOR'S JUSTIFICATION IS ITSELF FALSE.** Per-save distinct joined type words across the live library run 8 to 12 and NOT ONE SAVE REACHES 13 - the 13 is a UNION over a growing library, never the engine constant the docstring claims. Within the SAME version pair, 1239 records gives 8 words and 19837 gives 11, so "playing the game moves the tag count and leaves this alone" is exactly backwards. `NameProperty` is contributed by only 3 of the 12 tagged saves, so autosave rotation retiring those three turns `assert sweep.join.words >= 13` RED ON A CORRECT GRAMMAR - a live fragility, not a hypothetical. The companion claim "measured at the full observed width, so a thinned join cannot satisfy it" is refuted by a join thinned 3447 tags that satisfies it. **AMENDED 2026-08-16 (session 10) with a CLEANER counter-example and a NEW measured hazard, both re-derived by two agents independently.** FIRST, the cap-4 thinning already recorded here is beaten by `_MAX_TAGS_PER_PAYLOAD = 8`: it rots 1550 payloads with `join.tags` **IDENTICAL** at 55496 and `join.words` unmoved at 13 - a strictly cleaner demonstration that the distinct-word count does not track the thinning, because the tag count does not move at all. Note the pairing for whoever writes the replacement prose: cap 8 supports "a mutant rots payloads with the count unmoved" and does NOT support "drops thousands of tags", while cap 4 supports the second and not the first. Per-save distinct joined word counts measured across the library are `[8,8,8,8,8,8,8,11,11,12,12,12]`, every one below the floor of 13, which is the corpus-coupling this item exists to remove. SECOND AND NEW: **the floor's hazard is not confined to the join oracle.** Setting `_JOIN_WORD_FLOOR = 14` - which simulates autosave rotation retiring a rare word, the exact hazard - turns TWO tests red, not one: the join oracle at `assert 13 >= 14`, AND `test_every_tag_width_is_caught_by_a_library_backed_oracle`, which calls the join oracle inside its `already_red` check and dies with a message about mutants that never mentions the floor. So the attribution test does not avoid the hazard, it INHERITS it, and it fails misleadingly. The sentence claiming otherwise was deleted in session 10 rather than rewritten, per ADR 0008; the replacement is a detection claim and belongs to whoever closes this item.

### Acceptance

no assertion in `tests/save/test_decode_oracles.py` can go red because the operator played the game, and the cross-section oracle has a control that fails if its body is replaced by a green no-op


## CS-412

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: raised 2026-08-15 by the CS-407 result. FULL ENTRY relocated to this file under **CS-412 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: raised 2026-08-15 by the CS-407 result. The prior session's resume note for header 13 / save 42 said "the grid preamble is measured", and that measurement was recorded NOWHERE in the tree - not in `objects.py`, not in `synthetic.py`, not in the ledger - so the slice resuming it had to re-derive it from scratch. **A partial recorded as an adjective is not resumable.** The successor structure already exists as `LEVELLED_LAYOUT_OPAQUE_SPANS`; this item is about proving it COMPLETE against what the parser actually skips, so a later slice inherits evidence rather than a sentence. ADDED 2026-08-15: fold in `tests/save/synthetic.py:1093-1096`, which claims count equality for "2945 of 2945 levels on the (14,52) corpus". That is TRUE but narrower than reality - it holds on 6171 of 6171 levels across all four pairs, measured under CS-413. Found by the CS-413 builder and left alone because the file was outside its write-list, which is the boundary working as intended. A claim that is true and understated still rots, because the next reader treats its scope as the measured limit. Two precedents this session argue for generating such counts rather than writing them: CS-413's own first revision put a WRONG level count into a shipped docstring with a TRUE claim attached to it, and CS-404's evidence table now records which widths are measured versus merely uncontradicted rather than asserting a number.

### Acceptance

`tests/save/synthetic.py` carries a structure naming each unmeasured span by pair, offset role and width, and a test asserts every span the parser skips by length appears in it


## CS-401

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: detail relocated 2026-08-23 for budget to this file under **CS-401 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-23 for budget, not deleted. The item stays OPEN in
`ROADMAP.md`. This block is a LIVE instruction, not history.

REWRITTEN 2026-08-14. The original acceptance ended "and the ledger treats an unknown token as a new world rather than failing", which is NOT SATISFIABLE IN PHASE 4: the ledger is `clockspeed/advisor/ledger.py`, which is phase 5 and did not exist then (it landed under CS-500 on 2026-10-04). That clause moves to CS-500's acceptance, where the ledger exists. What remains here is the half phase 4 can actually prove, and it is the half that matters - the token is stable and the parser tolerates an unseen one.

### Acceptance

`WorldModel.token` is the header's saveIdentifier; two SYNTHETIC saves differing in name, play duration, chunk count and body content but sharing an identifier yield the same token, and a third with a different identifier yields a different one; a real-library test, skip-if-absent, asserts every save yields a 22-character base64url token, that the distinct-token count is strictly less than the file count, and that at least one token spans two different save versions - printing COUNTS ONLY and never a token value; and `load_world` on a token never seen before returns a normal `WorldModel` rather than raising


## CS-439

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16. FULL ENTRY relocated to this file under **CS-439 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: filed 2026-08-16. FIVE INSTANCES NOW - CS-417, CS-419, CS-430, CS-435, CS-438 - each a docstring promising a report over code that drops the value silently. **THE KEY IS MEASURED, NOT PROPOSED, and the first key tried FAILED the measurement, which is why this entry states both.** Key A, a reporting verb anywhere in scope, matches 292 of 298 functions on prose alone and the conjunction with the code half is also 54, so the prose half buys NOTHING - house style puts a reporting verb in nearly every module docstring. Key B, the verb in the function's OWN docstring minus a documented None-return contract, goes 298 to 106 to 25 to **12 candidates**, which is reviewable. **THE EVIDENCE THAT B IS REAL RATHER THAN PLAUSIBLE: it surfaces `clockspeed/save/workdir.py::_save_files` as a candidate, which is CS-438, FILED INDEPENDENTLY BY A DIFFERENT AGENT that did not build the key.** It also correctly classifies the CS-435 repair's own `usmap.text` and `usmap.resolve` as CONTRACT rather than candidates. Two known members to fold in: `workdir._mtime_ns` swallows `OSError` and returns 0, and `clockspeed/data/locate.py::_steam_library_paths` reads the Steam library index with `errors="replace"` so a replaced byte silently drops a library and the install reads as absent. STATED LIMITS, from the agent that measured it: CS-430's real content - a warning that FIRES but whose SENTENCE is false - is not statically decidable and needs the runtime discipline instead; the CS-419 aggregation-key collision is detectable but on a DIFFERENT key and is a second, cheaper guard; and an UNDOCUMENTED silent loss is invisible to B by construction, because anchoring on the promise is exactly what buys the reduction.

### Acceptance

a guard reports every function carrying a failure-exit edge that reaches neither a `raise` nor a warning sink while its OWN docstring promises reporting, with the sink set owned as data rather than prose, a control proving it fires on a planted instance, and each exemption carrying its own justification


## CS-440

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: **BUILT 2026-08-16 (session 12) AND REFUTED THE SAME DAY. The code shipped and the acceptance is met on NEITHER clause** - the subject delivered is a usmap POSITION, not a class, and the reason is a per-LOAD flag rendered as a per-ENTRY attribute. FULL ENTRY relocated to this file under **CS-440 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: filed 2026-08-16 as the stated remainder of CS-435, whose ledger entry names it. CS-435 closed on its written acceptance and its STATED DEFECT is not fully closed: a MODELLED class whose usmap name is undecodable STILL reports as unmodelled, and what changed is only that it is no longer silent. Two measured sites, both outside CS-435's write-list and neither touched: `clockspeed/save/world.py:919` builds `WorldWarning(source, code, detail, count)` and DROPS THE SUBJECT, so `name-0` never reaches a consumer and the world layer learns "some name did not decode" without learning which; and the reason set is `clockspeed/save/objects.py::REASON_CLASS_NOT_MODELLED`, "is not a class the supplied registry models", which is FALSE for this input and is the only member of `UNKNOWN_CLASS_REASONS`. This is a confident wrong answer surviving behind a correct warning, which is the non-negotiable 7 failure rather than the tolerated one. **BUILT 2026-08-16 (session 12) AND REFUTED THE SAME DAY. THE CODE SHIPPED AND THE ITEM DOES NOT CLOSE - THE ACCEPTANCE IS NOT MET ON EITHER CLAUSE.** The wiring is not vacuous - forcing the registry-loss flag constant reddens 3 tests and dropping the subject reddens 5, both byte-verified - and no CS-419 aggregation regression was introduced, because the world layer does no dedup at all. **CLAUSE 1 FAILS: THE SUBJECT IS A USMAP POSITION, NOT A CLASS.** The subjects delivered are `name-0` and `schema-0`; the name at that position is the empty placeholder and the schema was dropped, so a consumer learns WHICH POSITION failed and still cannot name the class. The class name is precisely the datum destroyed, and no amount of threading recovers it. **CLAUSE 2 FAILS BY TOTAL COLLAPSE:** the reason is a per-LOAD flag rendered as a per-ENTRY attribute, so injecting ONE unresolved-name warning into the real mapping gave the weaker reason to 1152 of 1152 entries and the stronger to none. On real data the new reason never fires at all - the branch is synthetic-only today. **AND THE KEY IS UNDER-INCLUSIVE IN THE DANGEROUS DIRECTION, which is this item's own defect class reappearing:** two further real conditions drop a declared class while the flag stays False, so the world still ships the exact false sentence. An unknown PROPERTY TYPE leaves the cursor mid-entry rather than skipping the payload; and **a newer usmap version - the realistic one, a game patch bumping the schema layout - needs no alignment luck**, which is one of the two routes the builder excluded untested while saying "if either can drop a class, my key misses it". It does. A sibling is worse: the unknown-property-type path can INVENT a name the file never declared, which is then reported MODELLED with no warning at all. Five false sentences, one of them ASSERTED into a control that pins the false claim.

### Acceptance

a consumer at the world layer can tell WHICH class failed to resolve, and `UnknownClass.reason` distinguishes "the registry does not model this" from "the name could not be decoded"


## CS-443

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: **THE UNFROZEN HALF WAS BUILT 2026-08-16 (session 12) AND REFUTED THE SAME DAY.** Three claims survived hard attack; the acceptance itself failed - the reporting channel has ZERO production consumers, so end to end a bad config is still silent. NEEDS ITS OWN FROZEN-FILE GRANT for `tools/precommit_gate.py`. FULL ENTRY relocated to this file under **CS-443 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NEEDS ITS OWN FROZEN-FILE GRANT for `tools/precommit_gate.py`; the 2026-08-16 CS-436 grant is SPENT and covers CS-436 alone. NOTE: filed 2026-08-16 by the CS-436 builder, MEASURED and deliberately not fixed because it is outside CS-436's three enumerated parts. With a malformed `config/local.json`, `discover_world_names` recovered 0 declared names and emitted NO skip about the config; the only line printed advises the operator to "add world_names to config/local.json", WHICH THEY HAD ALREADY DONE. That is the CS-436 false-statement class one layer up - not silence, an instruction to do the thing that is already done and is being discarded. `local_config` takes no `report` argument at all, so there is no channel to report on. Fold in the CS-436 residual its repair flagged and did not widen into: when the header reader is unimportable and the root is NOT truncated, "no world token is discoverable" still prints beside "the save-header reader is not importable", which is the same two-lines-that-disagree defect the CS-436 repair fixed for the cap case. **THE UNFROZEN HALF WAS BUILT 2026-08-16 (session 12) AND REFUTED THE SAME DAY. THE CODE SHIPPED AND THE ITEM DOES NOT CLOSE.** Three claims SURVIVED hard attack: all six loss paths report, each code is pinned by its own reddening test, and absence plus a valid file stayed silent across 1500 measured invocations. A SEVENTH loss path that CRASHED rather than discarded was found and fixed - `UnicodeDecodeError` is a `ValueError`, not an `OSError`, and escaped a function whose docstring promises it never raises; confirmed independently against the pre-fix blob. **WHAT FAILED, and the first one is the acceptance itself.** (1) **THE CHANNEL HAS ZERO PRODUCTION CONSUMERS.** No caller in `clockspeed/`, `tools/` or `scripts/` passes the collector, so `scripts/verify_env.py` against a malformed config still exits 0 printing nothing about it. The acceptance says a bad config "is REPORTED rather than returning `{}` in silence"; against every shipped entry point it still returns `{}` in silence. A resolver fix is not a consumer fix, and CS-452 carries the seam. (2) **THE `detail` SENTENCE - the entire operator-facing content - HAS NO CONTROL:** replacing all six with a nonsense sentence left the module suite green, and giving the malformed case the oversize sentence also stayed green. Only truthiness is asserted. That is the CS-430 class exactly. (3) **THE SUBJECT'S REDACTION FAILS OPEN TWICE** - it reads only the environment, and `_RESOLVED_ACCOUNT_NAMES` is lazily seeded so the same input redacts or does not depending on call order, with the config read running FIRST in the resolve chain. Its control is structurally blind because the oracle and the redactor share their only input. (4) Four sentences measured false, one of them the merger's. (5) FOUR further silent paths remain: an empty or whitespace value dropped later by `_override`, a duplicate key, and - the most likely operator error of all - a mis-typed or mis-cased key, returned faithfully and read by nobody.

## CS-446

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: detail relocated 2026-08-23 for budget to this file under **CS-446 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-23 for budget, not deleted. The item stays OPEN in
`ROADMAP.md`. This block is a LIVE instruction, not history.

filed 2026-08-16 by the CS-438 adversary and CONFIRMED by the CS-438 repair. `tests/save/test_phase4_gate.py:2108` declares `WRITER_WRITE_SURFACE` as a `frozenset[tuple[str, str]]`, so a sixth write duplicating an existing `(function, construct)` pair moves the raw site count from 5 to 6 and the test STAYS GREEN - measured by adding a second `open(mode="wb")` inside `_stream_copy`. The pin's own docstring claims a fifth mutating call is red, so the module contradicts itself about its own guard, which is the ADR 0008 shape outside `tests/save/`'s two fenced modules. Severity is real but bounded: the pin still catches a write in a NEW function, which is the more likely regression, and `clockspeed/save/workdir.py` remains the package's only writer. A set was the right shape for "which functions may write" and the wrong shape for "how many writes exist".

### Acceptance

adding a second write-capable construct inside an already-pinned function turns the pin red, and its docstring states what the pin does and does not catch


## CS-447

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 as CS-428's stated residual, measured rather than assumed, and deliberately kept out of that item because neither is a forced-failure render. FULL ENTRY relocated to this file under **CS-447 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: filed 2026-08-16 as CS-428's stated residual, measured rather than assumed, and deliberately kept out of that item because neither is a forced-failure render. **THE SESSION HEADER IS THE LIVE ONE AND ONLY ON LINUX:** pytest's `rootdir:` line prints the checkout path on EVERY run, pass or fail, and on a Linux CI runner the checkout sits beneath the runner account's home directory, so a home path is printed on every CI run of every lane. **THE LITERAL RUNNER PATH IS DELIBERATELY NOT WRITTEN HERE: the commit gate BLOCKED the first version of this entry for exactly that, which is CONVENTIONS section 10 and non-negotiable 3 doing their job on the entry that describes the leak.** It is harmless on this operator's machine because the checkout root is not under a home directory - which is LAYOUT LUCK and not a property of anything. The warnings summary is inside the region CS-428's own oracle scans but outside what its remedy can rewrite; CS-428 resolved that contradiction toward the statement and left the gap named and tested rather than implied. Also uncovered and confirmed by measurement: a collection error exiting rc 2, and `--co`.

### Acceptance

the session header and the warnings summary either carry no home path and no account name, or each is recorded as an exemption with a test asserting the exemption's own boundary holds


## CS-449

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-444 builder, which found it sweeping its own file and REPORTED rather than widened. FULL ENTRY relocated to this file under **CS-449 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-444 builder, which found it sweeping its own file and REPORTED rather than widened. **SECURITY-RELEVANT, SAME DIRECTION AS CS-444 - a WRITE.** `resolve_save_root()` returns None when its directory test is False, and a None root never becomes a candidate in `workdir._forbidden_roots()` at all, so CS-444's fix never sees this one: the hole is one layer below the layer just patched. **REACHABILITY IS EXPLICITLY UNMEASURED AND MUST NOT BE ASSUMED EITHER WAY** - it turns on which errnos the directory test swallows rather than re-raises, and the builder measured the SHAPE, not the exploitability, on 3.14/Windows only. Do not declare it unreachable without measuring on 3.13: CS-438 shipped exactly that error. **UPGRADED 2026-08-16 THE SAME DAY IT WAS FILED - THE REACHABILITY IS NO LONGER OPEN, IT IS MEASURED, AND IT REPRODUCES END TO END.** A security adversary drove a save root that is genuinely on disk, where the directory entry lists and `lstat` succeeds while `stat` fails: `is_dir()` answered False, `resolve_save_root()` returned None, `_forbidden_roots()` returned EMPTY, and a destination INSIDE that save root DID NOT REFUSE. `Path.is_dir()` applies no errno filter at all on 3.14, and the 3.12 filter already lists the same error, so the declared floor between them swallows it under either implementation. **HONEST LIMIT, STATED BECAUSE IT BOUNDS THE SEVERITY:** in that particular instance the destination is also unwritable, so the check is gone but the write would not land. The live variant is the transient one - the same call swallows sharing violations, access denials and not-ready errors identically, so a stat that fails at CHECK time and succeeds at WRITE time is the shape to fear, and the adversary could NOT construct a simultaneously-stat-denied-and-writable directory on this machine. A demonstrated MISSING CHECK, not a demonstrated write.

### Acceptance

a save root that EXISTS but whose directory test answers False for a reason other than absence is reported and does not silently become "no such root", proven by a test that fails against today's code, with reachability answered on the DECLARED FLOOR and not only on the interpreter this machine runs

### Recorded 2026-11-19 by wave 0 unit U-052.1: CS-444 folded into this row (plan ruling D88), NOT A COMPLETION RECORD

The folded row CS-444 (headline: Stop `workdir._forbidden_roots()` silently dropping a forbidden root it cannot
resolve) was folded into CS-449 by wave 0 unit U-052.1. Its ROADMAP line is gone and its leaf section is in
`docs/history_notes.md` under its id. Its acceptance, quoted verbatim, and graded separately at this row's close with
its own ledger record (D88):

> a forbidden root that fails to resolve is REPORTED and treated as still forbidden rather than omitted from the refuse list, proven by a test that fails against today's code


## CS-450

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-441 builder as a stated residual of its own work. Measured with byte-verified mutants: `exc.filename` yields no finding in a parameter-taking helper AND none inside a real handler, so it is not a parameter-scope gap at all but a named-field gap sitting identically on BOTH sides of the handler boundary, predating CS-441. It is genuinely undecided rather than merely unfixed - `tests/test_exception_rendering.py` ships a test asserting named-field renderings are NOT flagged, so a fix contradicts a shipped assertion and the two need ONE rule rather than a denylist. Same shape as CS-422: one file applying two evidence standards to itself with no stated rule.

### Acceptance

one stated rule governs `str(exc)` versus `exc.filename`, applied identically inside and outside a handler body, with the per-type redaction allowlist still unflagged


## CS-451

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-441 builder, reported and not touched as outside its write-list. A THIRD redaction helper, and unlike the two the sweep knows about it contains by WRAPPER rather than a per-type allowlist: it renders the object whole and wraps the result. **Containment-by-wrapper is not AST-readable**, so the sweep cannot grade it and an exemption would be an assertion rather than a check. Fold in that redactor's recorded limit - it rewrites paths under a home directory and leaves an absolute path NOT under one untouched - so the containment is itself partial. Do not close this by adding the helper to an exemption list; a hand-maintained list is what rots.

### Acceptance

the non-OSError branch of `_exc_text()` either stops rendering the exception whole or expresses its containment in a form the sweep can read, with the residual recorded against a stated rule


## CS-452

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-443 builder, reported and not widened into because the return types are consumed outside its write-list. `resolve_game_dir()` returns a labelled pair carrying a reason such as "set but not a directory", while `resolve_save_root()` and `resolve_account_dir()` return a bare optional path and discard the reason. That discarded reason is exactly what CS-449 needs and exactly what CS-443 had to invent a channel to carry, so this is the seam under both rather than a tidiness item. Consumers: `clockspeed/save/workdir.py`, `scripts/verify_env.py`, `tools/facts_probe.py`. Note `workdir.py` also calls `local_config()` without CS-443's collector, so a discarded declaration is still silent there.

### Acceptance

every resolver that can fail reports WHY in a single stated form, with each caller updated and the asymmetry recorded against that rule rather than per function


## CS-454

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-444 security adversary. FULL ENTRY relocated to this file under **CS-454 - detail**; read it before taking this item. **STATUS 2026-08-16 (session 15): BUILT, MERGED, ADJUDICATED, AND IT DOES NOT CLOSE. CLAUSE 2 MET, CLAUSE 3 MET, CLAUSE 1 NOT MET.** **The detail is RELOCATED 2026-08-18 (session 19), and is in this file under **CS-454 - status detail**, for the file's WARN budget. Relocated, not deleted, and it must be read before taking this item - it records which commits shipped, what the adjudicator ruled, and why clause 1 is the one still open.**

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-444 security adversary. **THIS IS A PRE-EXISTING LIVE LEAK, NOT ONE CS-444 INTRODUCED** - the adversary demonstrated it on an unpatched path as well - but CS-444 added a second echo path carrying it plus a green assertion saying it does not, which is worse than the bare leak. Measured in one supported configuration: the operator relocates saves via the env override and leaves the account directory undeclared. All three redaction rules then fall together - the positional rule needs a marker the relocation removed, the remembered-account list is fed only by an all-digit directory scan, and the digit backstop misses a hex token, a GUID and an operator-renamed directory. Epic-like, MS-Store-like and renamed account directories all rendered in plaintext; an all-digit one redacted. `clockspeed/data/locate.py` already names exactly those platforms as the reason not to rely on the digit rule. **THE CONTROL IS VACUOUS AND THAT IS THE HALF TO FIX FIRST:** removing the redactor from the new refusal branch entirely left the whole workdir suite green, for two independent reasons - the fixture's destination contains no account id at all, and its account name is all digits. Non-negotiables 3 and 12.

### status detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated 2026-08-18 (session 19) from CS-454's `ROADMAP.md` entry, which carried the file over its WARN budget. The item is OPEN and tier 1; its clause verdict stays in `ROADMAP.md` and only the supporting detail is here. Read it before taking the item.

The code shipped in `60068a9` and `02523f9` and STAYS - the relocated-path form is closed in all four resolution states, the 8.3 form is closed, and three independent vacuity reasons were removed from the controls. Full record in `docs/LEDGER.md` under the 2026-08-16 CS-454 non-closure entry. **FOUR THINGS REMAIN AND ALL FOUR ARE INSIDE THIS ITEM - do not file them as follow-ups, because a follow-up does not satisfy the clause it was filed against, which is what kept CS-422 open.** (1) **THE JUNCTION DEFECT, and it is in the NEW design rather than pre-existing:** `_remember_save_root` stores `_path_forms(str(path))` and never resolves, while `clockspeed/save/workdir.py`'s `_resolved()` deliberately does, so a save root reached through a junction can never match an anchor and a hex account directory rendered WHOLE through the production refusal in `_refuse_if_forbidden`. Reproduced with a real `mklink /J`. (2) **PLACEHOLDER INJECTION DEFEATS POSITION:** the environment pass runs first and rewrites a matching needle to a token, injecting `<` into the account segment; `_PATH_SEGMENT_CLASS` excludes `<>` so position cannot match and the name pass hunts a literal that is gone. With `USERNAME=Ada` and account directory `Ada4f3a...`, 30 of 33 characters render in plaintext WITH THE MARKER PRESENT. Pre-existing, unchanged from `bb7a236`, and a pre-existing instance of the defect this item names does NOT excuse it - this item's own detail entry opens by calling the leak pre-existing. (3) **THE WHITESPACE TAIL:** `My Backup Copy` renders `<account-dir> Backup Copy`. Three widenings of the segment class were measured and ALL THREE ARE WORSE - one eats the diagnostic prose, one leaves the terminal segment fully intact. Do NOT close this by widening the class; the adjudicator verified that decline was correct. The cheap route it names is feeding the matched segment into the name memory after position fires. (4) **THE BARE-SEGMENT FORM** must be closed or recorded as a STATED exemption bounded by `tests/test_redaction_scope.py`'s fence, which currently bounds it without any exemption being written down.

### Acceptance

an account directory that is not all-digits is redacted in every rendered message, proven by a control whose fixture uses a NON-digit account name, and the control fails when the redactor is removed


## CS-455

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: THE FULL NOTE IS RELOCATED to this file under **CS-455 - detail** and MUST be read before taking this item; it carries the measurements this entry rests on.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-18 (session 20) for budget, not deleted. The item
itself stays OPEN in `ROADMAP.md`.

filed 2026-08-16 (session 13) by the CS-421 builder as a MEASURED residual of its own work, and it is this project's own circularity one layer along. Measured with byte-verified mutants: replacing the whole fixed-width decode with a constant 1 leaves the two new byte-order oracles GREEN, because a small positive constant carries a zero high byte exactly as a real small value does. **THE ORIGINAL NOTE THEN SAID "constant 0 and a large constant both go red, so the blind spot is narrow" AND THAT WAS MEASURED FALSE 2026-08-16 (session 14), one process per constant so no memoised sweep carries a result forward: 0 red, 1 / 255 / 1000 / 65535 / 1000000 ALL GREEN, 16777216 red.** The accepting band is every constant with a zero high byte and a nonzero low byte - not narrow, and the acceptance above is widened accordingly. **THE RANGE FRAMING THAT USED TO SIT HERE - "roughly 1 to 16777215" - WAS MEASURED FALSE 2026-08-17 (session 16), one process per constant: 256 sits inside that range and goes RED, because its low byte is zero.** The two-part rule is the correct statement and the range was an approximation of it that is wrong at every multiple of 256. Deleted rather than re-fitted; do not write a range here. Do not re-derive this by looping mutants inside one process; the sweep is memoised and every later iteration silently reports the first mutant's verdict. **THE FIRST DRAFT OF THE DOCSTRING ATTRIBUTED THIS GAP TO THE ROTATION CONTROL AND THAT WAS FALSE** - under the constant-1 mutant 8 tests red, 7 of them synthetic-fixture tests and the eighth the nested gate that runs them, while `tests/save/test_properties.py::test_the_decode_collapses_when_the_payload_start_is_rotated` stayed green. It could not have done otherwise: it perturbs the WALK, and a fabricated value does not move the walk. So on the real library nothing catches this; only fixtures packed from the same belief the reader unpacks with do, which is CS-421's stated circularity reappearing. Do NOT close this with a synthetic fixture.

### Acceptance

a control that reads the real library goes red when `_decode_fixed_width` is replaced by ANY constant the oracles currently accept, without relying on a fixture this project packs


## CS-456

### NOTE - relocated from `ROADMAP.md` 2026-08-23

**NOTE RELOCATED for budget, never deleted: read this file under **CS-456 - detail** BEFORE TAKING THIS ITEM.**

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 27) for budget, not deleted. The item itself stays OPEN in `ROADMAP.md`. This block is a LIVE instruction, not history.

NOTE: filed 2026-08-16 (session 13) by the CS-422 builder against `TextProperty` alone, and **REWRITTEN TO THE FAMILY 2026-08-16 (session 14) after the CS-422 adversary measured that `TextProperty` is not the one honest exception but the one that happened to get transcribed.** Four type words ship a tag-extra width while their value reading is unmeasured - `ArrayProperty`, `MapProperty`, `SetProperty`, `StructProperty` - and only `ArrayProperty` is recorded in `DECLINED_VALUE_READINGS`. The other three are declined in `UNMEASURED_PAYLOAD_REGIONS` on SAMPLE SIZE, the criterion the rule disclaims, at 81, 72 and 45208 instances respectively; `TextProperty` sits in the new table on the same criterion at 10. Whether a wrong width is discriminated for ANY of them is UNMEASURED. Note the population must be derived: listing four names here recreates the hand-written scope that CS-458 exists to remove.

### Acceptance

for every type word that ships a tag-extra width while its value reading is unmeasured, either a control shows a wrong width for it costs something, or the decline is re-recorded against `WIDTH_SHIPPING_RULE` with a reason that rule admits, with the population DERIVED from the shipped tables rather than listed here


## CS-457

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: detail relocated 2026-08-23 for budget to this file under **CS-457 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-23 for budget, not deleted. The item stays OPEN in
`ROADMAP.md`. This block is a LIVE instruction, not history.

filed 2026-08-16 (session 13) by the CS-422 builder against its own work. Measured: citations written into `#:` doc-comments in `clockspeed/save/objects.py` resolved to TRUNCATED names and the checker PASSED - the underscore-wrap rejoin applies inside column-0 `#` blocks and not to `#:`, so four citations naming real tests were read as four dead names and nothing went red. Worked around by moving those citations into the adjacent `#` commentary block, where a planted dead name IS caught; the blind channel itself is untouched and is what this item covers. **THIS IS THE CS-442 FAMILY, one file along** - the verification pointer is the field that makes a claim trustworthy, and a channel the checker cannot read is a channel where a pointer rots silently. Note the failure direction is the dangerous one: an unreadable citation reads as no citation at all rather than as an error.

### Acceptance

a dead `path::test_name` citation inside a `#:` doc-comment turns `tests/save/test_oracle_citations.py` red, proven by a planted dead name, with the wrap normalisation applying there as it does in a column-0 block


## CS-458

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: THE FULL NOTE IS RELOCATED to this file under **CS-458 - detail** and MUST be read before taking this item; it carries the measurements this entry rests on.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-18 (session 20) for budget, not deleted. The item
itself stays OPEN in `ROADMAP.md`.

filed 2026-08-16 (session 14) by the CS-422 adversary and confirmed by the merger from source, no mutation needed. `tests/save/test_properties.py` builds its `shipped` set as `_TAG_EXTRA_STRINGS | _FIXED_WIDTH_VALUES | {GUID_BYTES, _SOFT_OBJECT_TAIL_BYTES}` and `CURSOR_WIDTHS | EXTENT_WIDTHS` equals that same union, so `ungoverned` and `phantom` are empty for any edit to either TABLE. **THAT PHRASING USED TO READ "structurally empty set differences" AND IT OVERSTATES, MEASURED 2026-08-17 (session 16):** the test transcribes `GUID_BYTES` and `_SOFT_OBJECT_TAIL_BYTES` as its own literals while `objects.py` spells them inline, so the two literals do NOT cancel and renaming `GUID_BYTES` in `CURSOR_WIDTHS` alone turns `ungoverned` RED. The acceptance below is unaffected - the table half is what needs independent sources - but the test was kept and re-docstringed rather than deleted, because deleting it would have removed a live transcription check. Five cursor-advancing widths in the same walk are covered by nothing: `clockspeed/save/objects.py::_TAG_INDEX_FIELD_BYTES`, `INT32_SIZE`, `UTF16_CHAR_SIZE`, the guid-flag byte literal and the `BoolProperty` in-tag byte literal. **THE ASYMMETRY IS WHAT REMOVES THE "PRIVATE CONSTANTS ARE OUT OF SCOPE" DEFENCE:** `_SOFT_OBJECT_TAIL_BYTES` is private and IS classified while `_TAG_INDEX_FIELD_BYTES` is private and is not, and nothing distinguishes them but who typed which literal. Mis-stating `_TAG_INDEX_FIELD_BYTES` reddens two census tests on their BASELINE with messages naming an innocent width, which is collateral collapse rather than grading.

### Acceptance

the governed set and the shipped set are derived from INDEPENDENT sources, proven by a mutant that introduces a cursor-advancing width without registering it and turns the partition test RED on a machine with no save library


## CS-459

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 (session 14) independently by BOTH the CS-421 adjudicator and the CS-421 adversary. **THIS ITEM OWNS THE TRUTH GAP UNDER CS-421 CLAUSES 1 AND 2** - it records that `WIDTH_ONLY_VALUE_TYPES` can become a lie in shipped data with nothing red, and a 2026-08-23 adversary reproduced exactly that. Detail relocated 2026-08-23 to this file under **CS-459 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-23 for budget, not deleted. The item stays OPEN in
`ROADMAP.md`. This block is a LIVE instruction, not history.

filed 2026-08-16 (session 14) independently by BOTH the CS-421 adjudicator and the CS-421 adversary, which is why it is filed rather than argued. The guard compares `EVIDENCE_FOR_VALUE_TYPE` to `_MAGNITUDE_SCORED_TYPES`, a hand-authored literal in `tests/save/test_properties.py`, never to what the oracles actually score - so the tie is between two transcriptions. Adding `EVIDENCE_MAGNITUDE` to `UInt32Property` IS caught; making the tally also score `UInt32Property` with the table untouched is NOT, and moves `int32_values` silently while `WIDTH_ONLY_VALUE_TYPES` becomes a lie in shipped data with nothing red. Neutering the `FloatProperty` scoring branch also leaves the coupling test green - only a separate emptiness floor catches it, so the docstring claiming the table is tied to the running controls overstates by one link, which is the ADR 0008 shape inside the control that grades ADR 0008 compliance.

**CONFIRMED AGAIN 2026-08-23 by the CS-421 control-validity adversary and re-checked by the merger.**
Moving `BoolProperty` off `declared_width` in `EVIDENCE_FOR_VALUE_TYPE` silently drops it from
`WIDTH_ONLY_VALUE_TYPES`, and the whole of `tests/save` stays green. The only non-module reader of
that set asserts it is non-empty and disjoint from the magnitude-scored set, and never that any
particular type is in it. **THIS ITEM ALREADY OWNED THAT FINDING** - the NOTE above names it in terms -
which is why no duplicate item was filed for it. The sibling gap on the vocabulary STRINGS is
different and is CS-827.

### Acceptance

an oracle that scores a type the table does not mark turns a test RED, proven by a mutant that scores `UInt32Property` while leaving the table untouched, with the scored population DERIVED from the oracles rather than transcribed beside them


## CS-460

### NOTE - relocated from `ROADMAP.md` 2026-08-23

**NOTE RELOCATED for budget, never deleted: read this file under **CS-460 - detail** BEFORE TAKING THIS ITEM.**

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 27) for budget, not deleted. The item itself stays OPEN in `ROADMAP.md`. This block is a LIVE instruction, not history.

NOTE: filed 2026-08-16 (session 14) by the CS-420 clause-5 adversary and CONFIRMED PRE-EXISTING by the merger - both the sentence and the `any()` it denies are present at 550d383, so no CS-420 commit introduced it. The comment claims the loop below it has "no any(), no short-circuit, no early exit"; there is an `any()` 33 lines below, inside that loop, and two asserts that exit it. **THE UNDERLYING PROPERTY IS SOUND AND THAT IS WHY THIS IS TIER 2:** the list comprehension that builds `fired` calls every oracle with no short-circuit, and the `any()` does string membership over that already-complete list, so no oracle goes uninvoked. The sentence is wrong about the code and right about the property, which is the ADR 0008 shape at its most deceptive - a reader checking the claim by reading the named loop finds the thing it denies. It survives the CS-420 fence because "no any()" carries no listed marker, which is that fence's declared under-detection direction working exactly as documented rather than a hole in it.

### Acceptance

the sentence is true of the code it describes, or is gone, proven by reading the loop it points at


## CS-462

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 (session 15). MEASURED: on a relocated save root holding only a hex-named account directory and no override, `resolve_account_dir` returns None, because `clockspeed/data/locate.py::numeric_account_dirs`' `child.name.isdigit()` filter is the ONLY auto-detection arm. `locate.py`'s own comments name Epic and the Microsoft Store explicitly as shapes that occur, so the module documents a case it cannot then resolve. **THIS IS SELECTION, NOT REDACTION, and it is deliberately NOT part of CS-454** - fixing it would incidentally cause the directory to be remembered and would close one CS-454 form as a side effect, and a side effect does not satisfy a redaction clause.

### Acceptance

`locate.resolve_account_dir` selects an account directory on a save root holding only a non-digit directory, with the selection rule derived from what the directory CONTAINS rather than from its character class, and a control proving an all-digit save root still selects exactly as it does today


## CS-465

### NOTE - relocated from `ROADMAP.md` 2026-08-23

**NOTE RELOCATED for budget, never deleted: read this file under **CS-465 - detail** BEFORE TAKING THIS ITEM.**

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 27) for budget, not deleted. The item itself stays OPEN in `ROADMAP.md`. This block is a LIVE instruction, not history.

NOTE: filed 2026-08-16 (session 15) by the CS-454 vacuity adversary and CONFIRMED by the merger using the fence's OWN helper. The walk is unbounded in DEPTH but grades against `RESOLVER_NAMES`, which is `locate`'s PUBLIC surface of six names, while the cycle it exists to prevent - `redact` to `resolve_save_root` to `_override` to `local_config` to `_read_local_config` to `_note` to `redact` - passes through FOUR private hops. Measured: a public-hop plant closes the cycle and reports two offenders, RED; a private-hop plant closes the identical cycle and reports NONE, GREEN, while the same tree raises `RecursionError` at runtime. **The comment above the test claims it reads the transitive closure precisely because "a single private wrapper would defeat a body-only check", so the module contradicts itself about its own guard** - the ADR 0008 shape inside a fence built to enforce ADR 0008. Note the fence declares no scope limit at all, unlike its sibling in `tests/test_redaction_scope.py`.

### Acceptance

a plant that closes the `redact` recursion cycle by entering it at a private helper turns `tests/data/test_phase2_gate.py::test_redact_calls_no_resolver_at_any_depth` RED, with the graded set derived rather than transcribed


## CS-467

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: detail relocated 2026-08-23 for budget to this file under **CS-467 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-23 for budget, not deleted. The item stays OPEN in
`ROADMAP.md`. This block is a LIVE instruction, not history.

filed 2026-08-16 (session 15). `test_no_planted_string_reaches_any_world_load_error_surface` already asserts over FIVE surfaces including the formatted traceback, which is the right design; but `_FAILURE_CASES` holds six CONTENT and parse failures only, all on files that exist with malformed bytes, and `_PLANTED_TOKENS` are all content markers. The one failure mode whose chained cause carries a path - a missing or unreadable save, where `OSError.filename` is the full save path - appears only in the message-shape test, which formats no traceback. **THE LEAK IS NOT LIVE and that is why this is tier 2:** the adjudicator measured that `workdir.py` builds `SourceUnreadableError` already-redacted, so the traceback renders `<account-dir>/<save-file>`. This is coverage, not behaviour - but the surface is guarded by another module's redaction rather than by this sweep.

### Acceptance

`tests/save/test_world.py`'s planted-marker sweep includes a failure case whose cause carries a path, with the path itself as the planted token


## CS-468

### NOTE - relocated from `ROADMAP.md` 2026-08-23

**NOTE RELOCATED for budget, never deleted: read this file under **CS-468 - detail** BEFORE TAKING THIS ITEM.**

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 27) for budget, not deleted. The item itself stays OPEN in `ROADMAP.md`. This block is a LIVE instruction, not history.

NOTE: filed 2026-08-16 (session 15) by the CS-454 vacuity adversary. `tests/data/test_locate.py` skips when there is no distinct 8.3 rendering, and `clockspeed/data/locate.py`'s `_win_path_form` returns None off Windows, while the tier-1 lane is `ubuntu-latest` and runs on every push. So the ONLY control that catches that mutant is skipped on every tier-1 run and graded solely by tier 2's Windows matrix job. Severity is coverage rather than correctness - there is no 8.3 leak where there are no 8.3 names - but a control that skips on the lane everyone watches is a control most readers will believe is running. **OBSERVED ON A REAL RUNNER 2026-08-16, so this is no longer a simulation:** the tier-2 `workflow_dispatch` on `8620238` skipped `tests/data/test_locate.py:858` on `ubuntu-latest` with the reason "this volume has no distinct 8.3 rendering", and the two operating systems differ by exactly four tests - `ubuntu-latest` 1977 passed 44 skipped against `windows-latest` 1981 passed 40 skipped, on an identical collected total of 2021. Do not re-measure this; measure instead which FOUR tests make up the gap, since only one of them is named above.

### Acceptance

the control that kills the `_remember_account_dir` long-name-only mutant runs, or is recorded as Windows-only with the lane that grades it named


## CS-464

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 (session 15). Same defect as the one CS-454 deleted from `tests/data/test_locate.py`, one file along and untouched because it was outside that slice's write-list: the test builds its "relocated" path as `local.joinpath(*locate.SAVE_ROOT_PARTS) / account_dir / "Backup"`, so the marker is still in the string and the positional rule catches every shape. **The test whose docstring names the relocation case is the one test that cannot fail for it.**

### Acceptance

the parametrized shape docstring no longer claims a character-keyed redactor would leak two of its three shapes, or the test is paired with a marker-absent sibling that observes it, proven one mutant per process


## CS-470

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: detail relocated 2026-08-23 for budget to this file under **CS-470 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-23 for budget, not deleted. The item stays OPEN in
`ROADMAP.md`. This block is a LIVE instruction, not history.

filed 2026-08-17 (session 16). The census reaches its terminator on more payloads under the identity than under any other of the 24 orderings, but the runner-up swaps only the two HIGH size bytes, which are both zero for any small declared size, so the two are separated only on the payloads carrying a size at or above the 16-bit boundary - a small population that the operator's play can remove entirely. **The test is gated to SKIP rather than to fail when that population is empty**, which is what keeps it out of the CS-432 false-red shape, and the gate is a stated bound rather than a fix. Note the asymmetry that produced this item: the session shipped the VALUE result as a candidate set of two and very nearly shipped this one as "exactly one of its twenty-four byte orders", on a smaller discriminating population than the one it had just called disqualifying.

### Acceptance

a discriminator distinguishes the identity from the ordering that swaps the two high size bytes on a population the census derives rather than on the payloads that happen to be large, or the census's own data records that it narrows to two and stops


## CS-472

### NOTE - relocated from `ROADMAP.md` 2026-08-23

**NOTE RELOCATED for budget, never deleted: read this file under **CS-472 - detail** BEFORE TAKING THIS ITEM.**

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 27) for budget, not deleted. The item itself stays OPEN in `ROADMAP.md`. This block is a LIVE instruction, not history.

NOTE: filed 2026-08-17 (session 16) by the CS-422 builder against its own work and reproduced by a verifier against the landed constants with the exception set re-derived: 4 of 5 per-entry deletions are caught and 1 is not. The uncaught word ships no tag-extra width, so it is outside the derived population and its entry is optional by construction. **The obvious derived closure is FALSE against the shipped tables** - requiring a decline for every word `UNMEASURED_PAYLOAD_REGIONS` records as unmeasured fails on two counts, because that table's keys are not all type words and a word recorded as unmeasured is not thereby a declined VALUE READING. So this needs a seam that separates those cases, not another assertion over the tables as they stand. The limit is recorded in `tests/save/test_width_rule.py` rather than left as an adjective. Adjudicated as NOT blocking CS-422, on the ground that a word shipping no width is outside a clause about when a width may ship.

### Acceptance

deleting any entry from `objects.DECLINED_VALUE_READINGS` turns a test RED, including an entry for a type word that ships no tag-extra width, with the required population DERIVED rather than listed


## CS-474

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-17 (session 16) by a control-validity adversary. The module imports the two TALLIES and then transcribes the two PIVOTS - the majority and minority comparisons the shipped oracles assert - so the derivation grades a copy of the judgement rather than the judgement. It is faithful today, verified against both shipped assertions. **The module's own import comment says a transcription of either would grade a copy instead of the shipped judgement**, so the file contradicts itself about its own method, which is the ADR 0008 shape inside a control built to escape circularity. The builder reduced the damage to one transcription per predicate with a single owner each, which is where an import would land.

### Acceptance

the byte-order predicates the survivor derivation applies are imported from the module that ships them rather than restated, or the restatement is tied to the shipped assertions by something that reddens when they diverge


## CS-477

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-18 (session 18) by the THIRD refutation of CS-476, after the second refutation's repair was believed final. **THE THREE MEASUREMENTS THIS ITEM RESTS ON - all at `tests/save` 1040 passed, exit 0 - ARE RELOCATED to this file under **CS-477 - detail** and MUST be read before taking this item;** they name the two open routes and the inert probe shapes exactly. **THE PATTERN THIS ITEM IS REALLY ABOUT:** each repair moved the hand-written seam up one level rather than removing it - label set, then site list. A fix that names a population is the defect; derive the population or state the bound.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-18 (session 20) for budget, not deleted. The item itself stays OPEN in `ROADMAP.md`.

**MEASURED, all at `tests/save` 1040 passed, exit 0.** (1) `_DISPATCH_SITES` in `tests/save/test_byte_order_status.py` is a hand-written 2-tuple; deleting one entry drops every oracle that entry owns and costs the probe NOTHING, because `_coarseness_observation` reaches its dispatch directly rather than through the tuple - so two line deletions inside that one module restore the zero-coarseness-call state the second refutation closed. (2) An ordinary extract-method refactor - moving `_tally_mantissa_coarseness` behind a helper called from the census - takes the call out of the scanned body while the oracle still runs, and EVERY control passes, which is stealthier than an alias because the neutering patch still bites. A rename dropping the `_tally_` prefix IS caught, but only by `monkeypatch.setattr` raising on a missing attribute, not by the derivation. (3) `_PROBE_VALUE_PAIRS` is graded by nothing: emptying it leaves the module green at 8 passed, and 3 of its 5 shapes cannot move anything under any combination, because both dispatch sites key on IntProperty and FloatProperty alone.

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

Close the reach control's remaining seam, where the oracles it requires are derived by NAME but the bodies it reads are still listed

### Acceptance

deleting a dispatch entry, or moving a tally call out of a dispatch body into a helper, turns a test RED, with the scanned population derived rather than enumerated; and the probe's value-pair population is graded by something that reddens when a pair stops contributing


## CS-479

### NOTE - relocated from `ROADMAP.md` 2026-08-23

**NOTE RELOCATED for budget, never deleted: read this file under **CS-479 - detail** BEFORE TAKING THIS ITEM.**

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 27) for budget, not deleted. The item itself stays OPEN in `ROADMAP.md`. This block is a LIVE instruction, not history.

NOTE: filed 2026-08-18 (session 19) by the CS-421 correctness refutation and re-measured by the merger before filing. **MEASURED:** displacing `tests/save/test_value_anchoring.py::_census_stored_patterns`'s read of `UInt32Property` leaves the derived set unchanged at 5 of the 7 offsets in [-3, +3] - the displaced bytes still carry the small-magnitude signature under both readings - and the universal predicate kills only +1 and -2. This is CS-421's own recorded circularity one layer along: the derivation establishes what the oracle SAYS, not that it was said about this type's bytes. **WHAT ALREADY HOLDS AND MUST NOT BE RE-DERIVED:** `test_no_fixed_width_value_depends_on_a_byte_outside_its_declared_extent` grades every fixed-width tag through `_anchored`, `UInt32Property` included, and reddens when the shipped reader's value start moves - so the SUITE holds the anchor and this control does not. What is open is a displacement applied to this derivation alone.

### Acceptance

displacing the separability census's own read by any non-zero offset turns a test RED, rather than being caught only by the sibling extent anchor


## CS-499

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-20 (session 25) as CS-498's disclosed residual, MEASURED: with `if module_path == Path(__file__): return` in `_assert_library_reach_is_declared` and an undeclared reaching helper appended to that same file, `tests/save` is GREEN at 1116 passed. CS-498's control compares two copies under different names in `tmp_path`, and a path-keyed exemption treats both as ordinary files, so they agree and it says nothing. **THE CANDIDATE NOBODY HAS MEASURED:** make the guard RETURN what it examined rather than None, and assert a non-empty examination for the real file - an early return then shows as an empty result instead of as silence. That changes the guard's signature and every call site, which is why it is filed rather than folded into CS-498. Do not close it by naming a path anywhere.

### Acceptance

a guard that early-returns when handed its own path turns a test RED on a machine with NO GAME INSTALLED, even though no control may modify the tracked source


## CS-492

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: nine rounds, nine refutations, every one on a real defect; the ESCAPE direction only, with rounds seven to nine BUILT and UNCOMMITTED. Detail relocated 2026-08-22 (session 32) to this file under **CS-492 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

### Relocated 2026-08-22 (session 32) from `ROADMAP.md` - the CS-492 NOTE, verbatim

Moved for budget, not deleted. The item itself stays OPEN in `ROADMAP.md`, which now
carries a one-line pointer here.

**NINE ROUNDS, NINE REFUTATIONS, every one on a real defect.** s27 graded round six (REFUTED), built and graded rounds seven and eight (both REFUTED on both lenses), and dispatched round nine, which is UNGRADED. **THE ROOT CAUSE IS LOCATED AND IT IS A CHOSEN CONTRACT: the evidence rule is VALUE-AGNOSTIC** - it asks whether a bare name is bound at module scope, never what to - so `stat = "chunks"` certifies `stat` as a filesystem primitive and a neighbouring `def get(self, stat): return stat` manufactures EIGHT declarations on the real `tests/save/test_phase4_gate.py`. That row is measured on rounds SIX, SEVEN AND EIGHT alike, so it predates every repair and round six's defect has been DISPLACED TWICE AND REPAIRED ZERO TIMES. **Rounds seven and eight are UNCOMMITTED in worktrees by operator decision** - no build is strictly best, r7 has the cleaner false-flag direction and three silent module-scope escapes, r8 fixes those and regresses three false-flag rows. **Do not close this by widening the name list alone** - CS-491's note said so and nine rounds have now tested it to destruction. **THE FALSE-FLAG DIRECTION IS NOW CS-807, TIER 1, AND IT OUTRANKS THIS ITEM** - operator decision 2026-08-22. This acceptance is ESCAPE-SHAPED and says nothing about flagging a module that reaches nothing, which is what actually refuted all nine rounds; read CS-807's detail block before taking either. **THE BARE-NAME CONFLICT IS MEASURED IRREDUCIBLE - do NOT spend a tenth round on it.** Two narrowing spikes, five-site and two-site, each take every manufactured-declaration payload to zero, each cost the SAME twelve controls, and narrowing the site count retires none: telling a caption from a locator on the same bare token needs the type resolution this repo has declined. Full measurement table, both failed fix shapes and the next action are in `WAKEUP_NOTES.md` session 27; the filing history is in this file **CS-492 - detail**.


Relocated from `ROADMAP.md` 2026-08-20 (session 24) for budget, not deleted. The item itself
stays OPEN in `ROADMAP.md`.

CS-492 - Close the reach routes that travel through an OBJECT rather than a name binding - acceptance: a module holding a primitive on an instance attribute, or serving one from a module-level `__getattr__`, and calling it from a function that names no primitive, turns a test RED on a machine with NO GAME INSTALLED - tier: 2 - NOTE: filed 2026-08-20 (session 24) as CS-491's disclosed residual, MEASURED by two refutation passes and re-measured by the merger. Two shapes, both green against the shipped guard: `self.finder = locate.resolve_save_root` bound in `__init__` and called from a sibling method or off a module-scope instance, and `def __getattr__(name): return locate.resolve_save_root` at module scope. **THE REASON THEY ARE NOT IN CS-491:** `_aliases_bound_in` deliberately holds module scope and function-local scope APART, because a local `finder` in one function says nothing about a name `finder` in the next - and an attribute bound inside `__init__` is a function-local binding whose CONSUMER is a different function. Making it module-visible re-opens the inversion the keying note records, and the correct fix is a per-CLASS scope that does not exist yet. **Both were ranked CONTRIVED by the adversary that found them**, and an AST scan of `tests/save` finds zero instances of either, so this is latent rather than live. Do not close it by making function-local bindings module-visible without measuring what that flags. **ALSO HERE, and NOT contrived:** a body held in a CONTAINER field - `parts: list` holding `[source.read_bytes()]`, or a helper returning `dict` whose value is the body - is not walked as a wrapper. That one sits close to CS-491's stated residual (the type is written nowhere) but is not identical to it.

### Acceptance

a module holding a primitive on an instance attribute, or serving one from a module-level `__getattr__`, and calling it from a function that names no primitive, turns a test RED on a machine with NO GAME INSTALLED


## CS-489

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-19 (session 22) by two refutation passes independently, on the same tree. The `ArrayProperty` entry reads "THREE OF THOSE FOUR WORDS ARE IN MEASURED_VALUE_TYPES AND Int64Property IS NOT, which is why it has its own entry below". On a tree that moves `Int64Property` into the measured set and deletes its region entry that sentence is FALSE and its pointer dangles, with the whole suite green. `tests/save/test_properties.py::test_the_region_table_holds_no_key_nothing_justifies` reads other entries' prose to JUSTIFY a key; nothing grades what the prose SAYS.

### Acceptance

an entry whose prose states another type word's classification turns RED when that classification changes


## CS-483

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-18 (session 21) by CS-482's mutation-grading pass, which found it INCIDENTALLY rather than as part of its brief and reported it against itself: the pass saw it fail once inside the phase-4 gate's nested subprocess while a mutant was being graded, then pass 3 of 3 standalone, and the full suite re-ran clean. It asserts on pytest's own frame-argument rendering from inside a sub-subprocess, which is the shape that goes load-sensitive. THE COST IS NOT A RED SUITE, IT IS A MISATTRIBUTION: a flaky test inside a mutation battery reads as a mutant DETECTED when the mutant is actually alive, and that error is silent and points the wrong way. Any future mutation work over `tests/save` is exposed to it.

### Acceptance

the test either passes deterministically under concurrent load, or it declares and enforces the isolation it needs, with a reproduction recorded either way

