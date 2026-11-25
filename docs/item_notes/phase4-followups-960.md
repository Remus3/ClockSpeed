# Clockspeed - live per-item detail, phase 4 - save reader, the CS-9nn block at CS-960 or above

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**THIS LEAF HOLDS THE `CS-9nn` BLOCK AT CS-960 OR ABOVE AND NOTHING ELSE.** Every section
in it was RELOCATED VERBATIM from `docs/item_notes/phase4-followups-900.md`, in the order
it stood there, by CS-1132 on 2026-09-17. That leaf keeps the rest of the block, below
CS-960, and `docs/item_notes/phase4-followups-1000.md` holds every phase 4 ID at CS-1000
or above. Its other siblings
`docs/item_notes/phase4-followups.md` and `docs/item_notes/phase4-followups-850.md` hold
CS-800 to CS-849 and CS-850 to CS-899 respectively. **NEITHER OF THOSE TWO SIBLING NAMES
SPELLS ITS RANGE HONESTLY**, so trust this sentence and the leaf membership rule in
`docs/item_notes.md`, never a filename.

**This is a leaf of `docs/item_notes.md`**, which owns the index and the rules this file
obeys. Read the index for the leaf membership rule routing every OPEN item, the verbatim
rule, and what this family never contains. Do not restate any of it here.

**What lands in THIS leaf.** Every OPEN item `ROADMAP.md` files under its `Phase 4`
heading whose ID is in the `CS-9nn` block at or above CS-960.

**THE SEAM IS AT CS-960 BECAUSE THAT IS WHERE THE BYTES SIT, AND IT IS THE FIRST SEAM THAT
IS NOT A BLOCK BOUNDARY.** The reasoning has ONE owner and it is not this header:
`docs/item_notes/leaf-membership-rule.md`, under `What CS-1132 changed`, which is the
annex `docs/item_notes.md` names as the owner of why each seam sits where it does. The
measured figures sit beside the seam constant in `tools/drift_guard.py`. Neither is
restated here.

**ONE RELOCATED BODY CARRIES A BARE "this leaf" POINTER AND IT STILL RESOLVES.** CS-962's
section says a status read "off this leaf" would have reported a shipped surface as
unbuilt. The pointer rule in `docs/item_notes.md` reads a bare "this leaf" as the leaf the
body sits in, and the body and its leaf moved together, so the sentence is as true here as
it was where it was written. It is named here rather than left to be rediscovered. No
other relocated body carries a "this file" or "this leaf" pointer, measured across every
section this leaf holds.

**CS-901 THROUGH CS-905 ARE NOT ALLOCATABLE**, and the measurement behind that sits in
`docs/item_notes/phase4-followups-900.md`, which owns the block's allocation record. All
five are below this leaf's floor in any case.

---

## CS-965

### FILED 2026-09-10 (session 80) from the CS-963 adversarial pass

**THE TREE STATES BOTH POSITIONS AT ONCE.** CS-852 decided that rendering a SIZE
while withholding the bytes is the safe default, and four shipped reprs do exactly
that. CS-963 then removed a length from two NEW `_Cursor.__repr__` methods, on the
grounds that the save's size is information `object.__repr__` never emitted. Both
cannot be right.

**THE FOUR SITES**, measured: `chunks.DecompressedBody.__repr__` renders the
decompressed payload length; `objects.ObjectRecord.__repr__` a body offset and
length; `objects.PropertyName.__repr__` three string lengths;
`header.SaveHeader.__repr__` a body offset.

**WHY IT IS NOT AN AGENT'S CALL.** CS-852 is a recorded decision. Reversing one
quietly inside a repair round is how a settled thing gets unsettled by accident,
and the argument runs both ways: a byte count is not a platform, an account id or a
player name, which is what non-negotiable 12 names - but it is derived from the
player's file and it is a fingerprint. The operator rules; an ADR records it.

### Acceptance

an ADR decides whether a size or an offset derived from a save is disclosure under non-negotiable 12, every one of the four reprs is brought into line with the ruling, and the CS-963 invariant arm grades the ruling rather than only whether a holder renders the planted marker - NOT to be settled by an agent alone, the operator rules

### Full headline

four shipped `__repr__` methods render a QUANTITY derived from the player's save while withholding its bytes: `chunks.DecompressedBody` the decompressed payload's length, `objects.ObjectRecord` a body offset and length, `objects.PropertyName` three string lengths, and `header.SaveHeader` a body offset - each a deliberate CS-852 choice recorded as the SAFE rendering, and CS-963 then removed exactly that kind of disclosure from two new `_Cursor.__repr__` methods on the grounds that a save's size is information `object.__repr__` never emitted, so the tree now states both positions at once and one of them is wrong


## CS-964

### FILED 2026-09-10 (session 80) from the CS-963 repair round, MEASURED not inferred

**WHAT IS BLIND.** Every planted-marker privacy arm under `tests/save/` decides by
`marker in repr(value)` with an ASCII marker, and every fixture builds its header
strings through `synthetic.fstring(text)`, which writes UTF-8 with a positive count.
`synthetic.fstring(text, wide=True)` exists and nothing used it before this session.

**WHY THAT IS THE WRONG ENCODING TO MEASURE.** `header._Cursor.string` selects
`utf-16-le` whenever the count on the wire is negative, which is what Unreal writes
the moment a string carries one non-ASCII character. The fields that carry personal
data are the session name and the player display name - the two a person types. So
the population of green privacy verdicts in this layer was measured against the
encoding those fields are LEAST likely to use on a real save.

**WHAT A RENDERER DOES WITH IT.** It prints the marker's letters each followed by a
null, which a person reads at a glance. The oracle returns an empty verdict. That is
CS-963's own defect one level up: an oracle that cannot observe the value it is asked
about passes for that reason alone.

**WHAT IS ALREADY DONE, so the next session does not redo it.**
`tests/save/test_header.py::test_the_marker_sweep_is_not_blind_to_a_wide_encoded_header_string`
pins the gap at one site and sweeps the wide spelling through the structural oracle.
`tests/save/test_header.py::_wide_marker_blob` builds the fixture by SPLICING the
narrow field for its wide spelling and asserting the splice landed, rather than by
writing a second header builder beside the first - a parallel builder is a fixture
that can drift away from the one every other arm uses.

**WHAT IS NOT DONE.** Every other arm. `repr()` of a wide slice renders escapes
rather than text, so an arm converted to the wide encoding must sweep with the
STRUCTURAL oracle (`test_properties::_structural_holders`) or compare bytes - moving
the marker constant alone would make it vacuous rather than wide.

### THE SEAM IS BUILT - MEASURED 2026-09-11 (session 81), branch `cs964-seam`

**THE ARMS COULD NOT BE CONVERTED UNTIL FIVE SHARED THINGS EXISTED, and only one
did.** Converting arm by arm would have produced thirteen copies of a helper
written thirteen ways, which is the fixture drift the fence above forbids.

1. `test_properties::_reaches_the_needle` ran the bytes question and the str
   question through ONE comparison. A bytes holder holds the WIRE spelling and
   must match byte-exact; a str holder holds DECODED TEXT, where the needle's
   wire encoding says nothing about what the holder contains. The old str branch
   asked `needle.decode("utf-8") in value`, and a UTF-16-LE needle DECODES fine
   there - every byte of wide ASCII is under 0x80 - into the letters each
   followed by a null, which no decoded string contains. It returned EMPTY, and
   empty is what every arm reads as a pass. `_needle_as_text` now asks which
   spellings could have produced the text; the bytes branch is fenced to stay
   exact, because a fix that matched liberally everywhere would be worse than
   the defect.
2. `_leaking_locals` and `test_header::_assert_free_of` asked for the ASCII
   spelling only. `_rendered_spellings` takes the escaped spelling FROM `repr`
   rather than interleaving a literal, since `repr` owns its own escaping.
   Widened at `_assert_free_of`, the chokepoint ten header arms funnel through.
3. `test_header::_markers_present_in` knew exactly one encoding AND asserted its
   count, so a spliced fixture reddened it with `encodes 1 markers, expected 3`.
   LOUD, NOT VACUOUS - the first survey called this vacuous and was wrong.
   Presence is now asked per marker across both spellings, because
   `_wide_marker_blob` is MIXED on purpose and one `encoding` parameter cannot
   describe it. `_spelling_of` lets an arm take its needle FROM the fixture.
4. `test_properties::_spliced_wide` publishes CS-963's splice out of
   `test_header` so the body-side arms share it. It REFUSES when the narrow
   field is not present exactly once.
5. `test_properties::_assert_the_needle_is_observable` is the control the
   acceptance clause names, in one line per arm. It refuses a (marker, needle)
   pair that does not describe one value - the trap named above in capitals -
   and its three checks are the three holder families this suite sweeps.

**THE BODY SIDE HAD NO WIDE ENCODER AT ALL, which the first survey missed.**
`test_properties::_fstring` hardcoded `text.encode("ascii")` with a positive
count and is the encoder for `test_properties`, `test_container_elements`,
`test_struct_interior`, `test_reference_resolution` and `test_world`'s planted
payload - and for `test_synthetic`, a SIXTH consumer this paragraph missed when
it was written and a verifier found on 2026-09-12. `wide` is keyword-only so
EVERY positional call site keeps its meaning, and it REFUSES an empty wide
string: `synthetic.fstring` returns the
NARROW spelling silently for that case, and a silent narrow fallback hands an
arm the exact encoding it was written to stop measuring. NO ARM MAY PLANT AN
EMPTY NAME OR VALUE.

**TWO COUNTS IN THIS SECTION DID NOT SURVIVE RE-DERIVATION, corrected 2026-09-12
by the verifier that graded the merge candidate rather than by the session that
wrote them.** The call-site figure was filed as 56 and re-derived as 47 by
tokenizing rather than grepping, against a baseline of 42 on `main`. It is now
spelled in NEITHER this note nor the encoder docstring: the property is that no
positional caller changed meaning, which needs no population size to state and
cannot be kept true by one. **AND THE ENCODER POPULATION IS NOT YET WHOLE.**
`tests/save/test_struct_interior.py` carries its OWN narrow-only `_fstring`
that the seam did not widen, so widening the shared encoder did not reach that
module's planted payloads. That is a residual for the remaining conversions and
is the kind of parallel builder the fence above forbids - it must be folded into
the shared encoder rather than widened in place.

**ONE ARM OF FIFTEEN IS CONVERTED.**
`test_header::test_planted_markers_never_reach_any_surface` is parametrized over
the spelling - 3 header versions x 2 encodings. EVERY DERIVED OFFSET IS
RE-DERIVED PER SPELLING: the wide fields are longer (the header goes 148->203,
176->231, 206->261 bytes), so the truncation loop takes its bound from the
RESPELLED header. Bounded by the narrow length it would stop short of the wide
string block and never enter the frames the arm is about - that is how this
conversion would have been vacuous.

**AND THE WIDE DRIVE ON THAT ARM IS NOT YET SHOWN LOAD-BEARING. Say so rather
than rounding up.** The leak mutant - a truncation refusal quoting the 64 bytes
it refused - is killed 6 of 6 with the mutation asserted to have landed and the
pristine floor measured first. But holding that mutant AND reverting piece 2 to
its ASCII-only question still kills the WIDE cases 3 of 3, because the mixed
fixture leaves the save-name marker in ASCII and the leaked dump carries it
whatever the other two fields are spelled. The asymmetry an adversary DID
measure was `_value_surfaces` over a dataclass field carrying a wide slice, and
the guard for that is piece 2's own wide-encoded-raw-slice arm in
tests/save/test_header.py, which fails without piece 2. That arm is NOT NAMED
HERE as a citation because it does not exist on main - it lands with the
cs964-seam branch, and a doc on main that cites it is asserting something this
tree cannot resolve. The experiment that would separate the two on the population
arm is a field-specific mutant dumping only the session slice.

### THE EXPERIMENT WAS RUN - MEASURED 2026-09-12 (session 87) BY AN ADVERSARY, AND IT ANSWERS AGAINST THE SEAM

**THE LOAD-BEARING CLAIM IS REFUTED AS A GENERAL CLAIM.** Do not restate it. The
field-specific mutant the paragraph above named as decisive was built: `parse_header`
captures the session-name field's exact wire slice onto the cursor after `skip_string`,
and `_Cursor._require` attaches ONLY that slice - not the 64-byte dump - as a note on the
truncation refusal. Landing was asserted by a substring check before every run, and the
pristine floor was measured three times.

**IT IS SYMMETRIC. Narrow kills it 3 of 3 and so does wide.** By the criterion this item
set for itself, the wide half buys nothing on that mutant. The kills are genuine rather
than riding the narrow save-name marker - narrow reports the leak as
`'MarkerCharlieSessionNeedle'` and wide as `'M\x00a\x00r\x00k\x00e\x00r\x00...'` - so
the mixed-fixture confound the paragraph above worried about is resolved in the seam's
favour, and the question is still answered against it.

**AND THE WIDE DRIVE'S WIDENESS WAS ITSELF UNGRADED, which is worse than the symmetry.**
Reducing `_respell` to `return data`, so the wide ids became byte-identical duplicates of
the narrow ones, left the WHOLE of `tests/save` green at 1511 passed, exit 0. Nothing
anywhere noticed that the wide half of a parametrization named for its encoding was not
wide. `_spliced_wide` has its own arm; the ARM'S USE of it had none - the same defect one
level out, a fixture property deciding what a whole parametrized population measures and
graded by nothing. **REPAIRED at the merge, post-verdict**: the arm now asserts the
respelled blob differs from the narrow one, carries the session marker in its WIDE
spelling, and does NOT still carry it narrow. That mutant now fails the three wide cases
and leaves the three narrow ones untouched.

**ONE MEASURED EXCEPTION, and it is the reason the seam is not merely decorative.** A
mutant retaining the payload on the wide branch of `_string_extent`, gated to header
versions 10 and 13, is killed by `[wide-10]` and `[wide-13]` AND BY NOTHING ELSE IN 1511
TESTS. So the wide half does hold unique cross-version coverage of that `count < 0`
branch. **That coverage is real and was, before this repair, unprotected.** The
ungated form of the same mutant is caught by the pre-existing
`test_the_marker_sweep_is_not_blind_to_a_wide_encoded_header_string`, so only the gated
form isolates it.

**THE FIVE PIECES, GRADED INDIVIDUALLY.** Piece 1 (`_needle_as_text`) reduced to a single
UTF-8 decode fails the wide cases 3 of 3 - graded. Piece 3 (`_markers_present_in`) reduced
to the UTF-8 question fails wide 3 of 3 - graded. Piece 2 is graded by its OWN arm rather
than by the converted arm: a sweep-only revert at `_assert_free_of` leaves all 6 cases
passing and reddens only `test_the_surface_sweep_is_not_blind_to_a_wide_encoded_raw_slice`.
Piece 4 is the one the repair above closes. **Piece 5's own revert was NOT RUN and stays
UNMEASURED** - do not record it as graded.

**THE CONTROL CAN REFUSE, BUT ITS ONE SHIPPED CALL SITE IS VACUOUS FOR THAT HALF.**
`_assert_the_needle_is_observable` correctly refused all six malformed pairs put to it -
a wide needle of different text, a narrow needle of different text, needle a prefix of the
marker, marker a prefix of the needle, an empty needle, a one-byte needle. But the call
site in `test_header` passes `_spelling_of(marker, blob)`, which DERIVES the needle from
the marker, so the pair is consistent by construction and the pair-mismatch trap this note
names in capitals can never fire there. Only the oracle-blindness half is live at that
site. **A later conversion must not cite that call site as evidence the trap is graded.**

**THE SURVEY'S EXCUSING RULE WAS REFUTED, so do not rebuild the population from
it.** The rule was "a decoded-str oracle sees ASCII at either encoding,
therefore that arm is narrow-sufficient". `test_header::_value_surfaces` and
`repr(error.args)` are TYPE-AGNOSTIC ASCII sweeps, and `repr(bytes)` is a str by
type and raw bytes by content; `isascii()` does not rescue it, because the
escapes are themselves ASCII. Its conclusions happen to hold at `de9cb6d` only
because no bytes-typed field is currently reachable from those chains - a fact
the survey never checked. Also from the refutation, and worth keeping: the
`MAX_STRING_BYTES` cap is applied POST-MULTIPLY, so characters 8192..16383
refuse wide and parse narrow. No arm plants in that window today.

**STILL NOT DONE.** Twelve WIDE-REQUIRED arms - four in `test_header`, nine in
`test_world`, minus the one converted - plus the two ON-WIRE arms the first
survey never opened, `tests/save/test_container_elements.py::test_no_repr_the_container_decode_adds_renders_an_element_s_bytes`
and `tests/save/test_struct_interior.py::test_no_repr_the_struct_decode_adds_renders_a_name_a_value_or_a_word`.
The NARROW-SUFFICIENT arms still owe the sentence in their own text saying why
one encoding is enough for the value they plant. Nothing in the seam is
mutation-graded except the one arm above.

### Acceptance

every planted-marker arm in `tests/save/` is driven at BOTH encodings, or names in its own text why one is sufficient for the value it plants, with a control per arm proving the sweep reddens on the wide spelling when the value IS present, and the fixture builders emit a wide string without a second header builder being written beside the first

### Full headline

every privacy arm in the save layer hunts an ASCII marker inside `repr(value)`, and Unreal writes a header string as UTF-16-LE with a negative count the moment it carries one non-ASCII character - which the fields carrying personal data, a session name and a player display name, routinely do - so the whole population of green verdicts in that layer was measured against an encoding those fields do not use, while a renderer prints the wide bytes legibly; CS-963 pinned the gap at one site in `tests/save/test_header.py::test_the_marker_sweep_is_not_blind_to_a_wide_encoded_header_string` and left the rest


## CS-962

### SLICE S0 MERGED - the panel seam - MEASURED 2026-09-09 (session 78)

**WHAT THE SEAM IS.** Every dashboard panel wanted to edit `app.js` and
`index.html`, which would have made four panels one ordered queue. S0 publishes
`registerPanel(id, mountFn)`; a panel receives a DOM root and the
ALREADY-FETCHED payloads and never issues its own fetch, so `app.js` keeps sole
ownership of I/O and its sequential-probe discipline is untouched. A panel whose
mount throws does not stop the others - measured by removing the guard and
watching three arms redden, not asserted.

**THE DECOMPOSITION PROVED ITS OWN DISJOINTNESS AND STILL COLLIDED, AND THAT IS
THE LESSON.** The planner enumerated fifteen paths, proved no two slices shared
one, and the write-list was still wrong: `tests/surface/test_server.py` pinned
the static surface at exactly three names, in a file no slice had listed. Adding
a panel module reddened it unconditionally. **A WRITE-LIST IS DERIVED FROM WHO
WRITES, AND THE THING THAT BREAKS IS WHOEVER READS.** The next decomposition
must ask what ASSERTS on a value, not only what edits a file. The builder
correctly refused to widen its own write-list and reported the collision
instead; the merger repaired it.

**THE COUNT IS NOW DERIVED, NOT RETYPED.** That arm's constant reads the
server's own table rather than a hand-kept literal, because a count maintained
in two files is a count that will be updated in one. The NAMES stay spelled out
- that half catches a module served by accident, which a derived count cannot.

**AN ID COLLISION THE MERGER CAUSED.** The builder had no roadmap item and
allocated `CS-960` itself, saying so plainly and filing nothing. The merger had
allocated the same id to the decode work in the same session, from the same
"highest is CS-959" reading. Ten references were moved to CS-962 at merge.
**TWO AGENTS ALLOCATING FROM ONE HIGH-WATER MARK IN PARALLEL WILL COLLIDE** -
the id must come from the dispatch, not from the builder.

**WHAT IS NOT MEASURED, carried from the builder's own report.** No real browser
ran: the behavioural arms use a hand-written DOM stand-in under node, so layout,
focus and the `defer` load order are NOT graded - `defer` is asserted as markup
only. A CS-600-style Chromium pass over the new panel host is owed. The node
dependency is new to the Python suite and fails loudly rather than skipping, but
whether node is on PATH in the tier-2 CI job was not verified here.

**THE LINE THAT STOOD HERE WAS TRUE ON 2026-09-09 AND IS NOW FALSE.** It said the
four panels - registry browser, solve bench, warnings list, scope note - were
stubs that rendered nothing. All four were built, and three more arrived after
them: `panel_map.js`, `panel_optimize.js` and `panel_power.js`. Seven panels, 263
to 744 lines each. Corrected 2026-09-14, after a status read off this leaf would
have reported as unbuilt a surface that ships.

**READ THIS ITEM'S LEDGER ENTRY FOR ITS STATE, NOT THIS SECTION.** The entry
dated 2026-09-13 is the current one and it is precise: of the acceptance's four
clauses, two are discharged plainly, the exactness clause was verified by an
adjudicator who did not write it, and ONE IS UNTESTED. That last one is the whole
of what keeps CS-962 open - the page must state plainly which of its panels are
registry-derived and which are world-derived, and name what it cannot show.

**SO THE REMAINING WORK IS THE PAGE DESCRIBING ITSELF, NOT A PANEL.** A session
picking this up is writing provenance and limits into a page whose panels already
work, which is a different job from the one this section used to describe. That
is why the stale line is corrected here rather than deleted: the correction is
the routing information.

### OPERATOR DECISIONS ON THIS ITEM - FILED 2026-09-09, do not re-litigate

- **THE PAGE MAY POST, FOR SOLVE.** `app.js` carries a written rationale headed
  "WHY THIS PAGE ISSUES NO POST AT ALL", grounded in request forgery against a
  long-lived loopback page. The operator reversed it for the solve bench. Two
  facts made the trade cheap: the server reads NO request body anywhere, so a
  POST here is a query string with a different verb, and solve and optimize are
  pure reads that happen to be registered POST. **THAT RATIONALE BLOCK IS NOW
  FALSE AND MUST BE REWRITTEN BY WHOEVER LANDS THE SOLVE PANEL** - it lives in
  `app.js`, which no panel slice may touch, so it is a merger's edit.
- **AN EXACT RATIONAL IS RENDERED AS THE PAIR PLUS A MARKED DECIMAL.** `7/3` is
  the truth and is shown; a rounded decimal sits beside it, explicitly labelled
  an approximation for display. The float never enters a decision path.
  *Do not re-pitch:* rendering the decimal alone.
- **`byproduct_policy` IS PRESELECTED AS `balanced` AND SHOWN AS AN EDITABLE
  FIELD**, not hidden. The page makes the modelling choice visibly rather than
  making the player answer it before their first result.
- **NODE COORDINATES MAY BE PUBLISHED.** The resource-node actors are decoded
  with exact translations and the wire carries only a count. The operator ruled
  they may go on the wire - node purity and resource type are NOT in the save,
  so a node panel shows placement and class only. This is a new endpoint plus a
  panel, not a UI-only slice, and it is unbuilt.

### NOTE - filed 2026-11-25 by the session 159 plan

H1. The Scope panel prints, for every id in `data.panels`, one line `<id> - <sources>` under `PANELS REGISTERED ON THIS PAGE`, sources drawn from the closed set registry-derived, world-derived, health-derived (two joined by ` and `). Arm: `test-every_registered_panel_is_stated_with_its_sources` in `tests/surface/test_panel_scope.py`.
H2. Negative: a registered id missing from the table renders `<id> - UNCLASSIFIED` and ``test-every_shipped_panel_module_registers_a_classified_id`` goes red (proved by ``test-deleting_one_classification_turns_the_census_red``).
H3. Negative: a classified id no shipped module registers goes red: ``test-a_classified_id_that_no_module_registers_turns_the_census_red``.
H4. Close: an adversary on a frozen SHA, then a distinct adjudicator, grade all four hub clauses on Scope as mounted on System (D52 reading); the record also confirms no glance model is built here (D120: any glance view reads `GET /api/glance`).

### Acceptance

a person can look up a recipe and ask what a target rate costs in machines and raw inputs, every rate rendered from the exact `{num,den}` the wire carries with no division anywhere in the render path, the page states plainly which of its panels are registry-derived and which are world-derived and names what it cannot show, and no panel issues its own fetch - proven by an arm per panel against synthetic payloads plus a seam arm that reddens when a panel is served but not registered

### Full headline

the dashboard is a SELF-DIAGNOSTIC rather than a player's tool: it renders its own health, its own route table, six world version scalars, five counts and the unmodelled-class list, and nothing a person playing the game would act on - measured across the whole surface, `/api/registry` is fetched on every refresh and only its HTTP STATUS reaches the DOM so not one item, recipe or building name is ever displayed, `/api/solve` and `/api/optimize` answer 200 against real data and the page never calls them, and `/api/world` serves a warning list the page renders as a bare number


## CS-982

### Filed 2026-09-11

The `(14,60)` property tag carries a flags bitfield where the legacy shape carries a guid
flag. Three bit values were observed across the real record population and one was not
observed at all; an unobserved bit REFUSES the payload rather than assuming a width, which
is non-negotiable 7 and is the right default.

**THE WEAKNESS IS IN AN OBSERVED BIT, NOT THE UNOBSERVED ONE.** The bit read as adding an
int32 was seen on two tags in one record. Dropping that reading costs exactly one record,
which is the only discriminating evidence there is for it. Two tags is not a measurement of
a field width; it is a hypothesis that happens to close the walk.

**DO NOT close this by re-running the same population.** The same two tags will be there.
What would settle it is a tag of that shape whose value can be read back independently, or
a second save carrying more of them. The honest alternative is to record the width as
unmeasured and refuse it, exactly as the unobserved bit is refused - which costs one
record's payload and buys a claim that is true.

### Acceptance

the bit that adds an int32 is graded by an arm driving more than the two tags it currently rests on, or its width is recorded as unmeasured and the payload refuses it as an unobserved bit already does


## CS-983

### Filed 2026-09-12 by the session 86 merger, from an adversarial refutation

**WHAT THE ADVERSARY FOUND, AND IT IS NOT REPAIRED BY ARGUING WITH IT.** CS-981's routing
slice decided CS-G05 out of `docs/GATED.md` and did not move its body, because the leaf the
routing table names for it - `docs/item_notes/phase4.md` - was outside that slice's
write-list. Declining to self-widen a write-list was the right call. The state it left is
not: `docs/GATED.md` now holds a section asserting, in its own words, that CS-G05 does not
meet that file's membership rule - "gated means no amount of work inside this repo can close
it" - while the section stays in the file. A section that fails its file's own rule and
stays is incoherent under that rule, whatever the reason.

**WHY THIS IS A SEPARATE ITEM AND NOT A REPAIR FOLDED INTO CS-981.** Routing CS-G05 out
needs an ACCEPTANCE CLAUSE written for it, and CS-G05 has never had one - it is a gate with a
DRAIN half, not an item with a clause. Writing one is a scope decision, and the slice that
took the routing decision deliberately refused to improvise it inside a status block. The
refusal is right and is preserved. This item is where the clause gets written on purpose.

**THE TWO ROUTES ARE BOTH OPEN AND THE ITEM DOES NOT PREJUDGE WHICH.** Either CS-G05 gets a
clause and a `ROADMAP.md` line with its body relocated, or the decided-out declaration is
WITHDRAWN and the section states a condition that is genuinely outside this repository.
The second is a real option, not a formality: the STATUS 2026-09-03 block records that all
nine files of the pair are ONE world played forward, so a drain needing independent WORLD
GENERATION still needs more play, and that is an external condition. Which drain CS-G05's
residue actually needs is the measurement this item turns on.

**WHAT IS OWED EITHER WAY.** `tests/save/test_properties.py::test_save_60_refuses_the_grammar_the_other_pairs_accept`
is vacuous - it passes because its sweep carries its own independent reader of the LEGACY tag
grammar, so its zero is a true statement about that grammar and a false one about the save.
CS-G05's own status block says correcting it is a separate slice and that until then its
green may not be cited for anything. It is the one residue no other item owns, and it does
not become owned by CS-G05 being moved.

**DO NOT RENAME THAT TEST.** `docs/LEDGER.md` and `docs/history_notes.md` both cite it by
name and both are append-only, so a rename rots two citations in records that are never
edited. Session 85 took that decision deliberately and narrowed the docstring instead.

**A CONTRADICTION THIS SESSION CREATED AND DID NOT FIX, recorded so it is not discovered as a
surprise.** `docs/item_notes/phase4-followups.md` under CS-847 says two prose hand-offs in
`clockspeed/save/objects.py` are "harmless only while `CS-G05` stays GATED. If it closed
while those sentences stood, the module would stay green." The decided-out declaration
contradicts the precondition of that sentence without firing its trigger, since routing out
is not closing. Measured 2026-09-12: no guard keys on membership of `docs/GATED.md` at all,
so nothing mechanical fires today. CS-847 owns that text and this item does not edit it.

### Acceptance

`CS-G05` either carries an acceptance clause and a `ROADMAP.md` line with its body relocated to the leaf `docs/item_notes.md` names, or its status block records a condition that is actually outside this repo and the decided-out declaration is withdrawn, with the vacuous PREP harness `tests/save/test_properties.py::test_save_60_refuses_the_grammar_the_other_pairs_accept` owned either way

### Full headline

`CS-G05` is decided out of `docs/GATED.md` and its body has not moved, so a section asserting it does not meet that file's own membership rule is sitting inside that file


## CS-984

### Filed 2026-09-12 by the session 86 merger, measured before filing

**THE SEAM GAP, MEASURED RATHER THAN INFERRED.** `clockspeed/save/objects.py` decodes 774
top-level struct interiors on the pinned development world after the CS-829 grammar carry.
`clockspeed.save.world.RecordProperties.values` carries ZERO of them. Measured this session
with a read-only probe reporting counts only: `struct_values_top_level 0` both before and
after the carry, against 774 interiors the reader produced. They land on
`objects.PropertyResult.struct_interiors` and the world layer never reads that field.

**WHY THE VALUE MAPPING IS THE WRONG HOME AND THE ITEM DOES NOT PREJUDGE THE RIGHT ONE.**
`_walk_payload`'s own comment states the separation as the design: "A SEPARATE POPULATION
FROM `properties`, AND THE SEPARATION IS THE DESIGN - CS-829. The interior is REPORTED here
and the struct word stays OUT of `MEASURED_VALUE_TYPES`", because promoting the type on the
strength of the form it DOES read would claim a top-level value reading for every struct
including the native ones. So the fix is NOT to drop interiors into `values` alongside the
scalars. What shape it should take is this item's design work.

**THE HARD PART IS THE PROPERTY NAME.** `struct_interiors` is a FLAT TUPLE with no name
attached, so a consumer cannot tell which property an interior came from. Inventory needs
exactly that join - a building holds an `ObjectProperty` reference to a separate inventory
component, and finding the stacks means naming the property that holds them. An interior
population with no names is not usable by `clockspeed/audit/` for this purpose.

**WHY THIS IS SEPARATE FROM CS-981 RATHER THAN PART OF IT.** CS-981's acceptance turns on
`/api/map` serving a non-empty inventory. That needs this seam AND the join above it. Filing
one item for both would hide a measurable seam change behind an unmeasured join, which is the
shape `docs/GATED.md` warns about one level up.

### Acceptance

a `StructProperty` interior that `clockspeed/save/objects.py` decodes is reachable from `clockspeed.save.world.WorldModel` with its property NAME attached, so `clockspeed/audit/` can join a building to what it holds, proven by a test that goes RED when an interior the reader decoded is dropped at the seam, and by a real-library arm reporting COUNTS ONLY that the published interior count equals the reader's


## CS-986

### Filed 2026-09-12 by the session 86 merger, from the CS-829 repair round's own stated limit

**WHAT IS UNMEASURED.** The repair makes a CONTAINER whose tag carries
`TAG_FLAG_NATIVE_SERIALIZE` refuse a derived width and route to unmeasured. It deliberately
does NOT extend that refusal to a `StructProperty` tag carrying the same bit whose interior
nonetheless decodes as a tag list. Whether such a tag is read correctly is unknown, and no
corpus instance is known in either direction.

**WHY THE SCOPE WAS RIGHT AND MUST NOT BE WIDENED CASUALLY.** Extending the refusal to
interiors would move the top-level decoded-value population that the whole CS-829 grammar
carry rests on - the 803 values whose disagreement went to zero. A change that moves the
denominator of the result it is checking cannot be graded against that result. Measure the
population FIRST and decide after.

**DO NOT CLOSE THIS BY ASSERTING A ZERO.** An assertion over an empty population satisfies
every zero, and a bare zero is not a measurement. If the population is empty, the item closes
by reporting the population AND the fact that it was looked for, not by an `assert count == 0`
that would pass on a reader that found nothing at all.

### Acceptance

the population of such tags is measured over the library and reported as a count, and the interior reader either refuses them or states in a test why admitting them is evidenced, without moving the top-level decoded-value population the CS-829 grammar carry rests on


## CS-966

### Acceptance

the two populations are compared STRUCTURALLY rather than by a case table, covering both the marker SET and the keying, proven by two mutants that redden - one adding a marker field to one side only, one planting a duplicate `ClassName` on a power-bearing entry

### Full headline

CS-210's census claims to count the REGISTRY-PUBLISHED buildings, and two independent routes let that population drift from what `clockspeed/data/registry.py` actually publishes without any arm reddening - MEASURED 2026-09-10 by an adversarial lens against the closing tree: (a) the predicate fence `tests/data/test_registry.py::test_the_census_building_predicate_agrees_with_the_registrys` is a seven-case VALUE table, so adding a third marker field to one predicate only is not caught - probed with `mEstimatedMininumPowerConsumption` and it passed; (b) the census counts docs ENTRIES while the registry publishes a `ClassName`-keyed dict, so an entry with a missing or duplicate `ClassName` is counted and never published - on this build the two coincide exactly at 68 so it is latent rather than live

## CS-967

### Acceptance

the parallel whole-tree spelling and its `--dist loadfile` requirement are stated wherever a worker is instructed to run the whole tree, and a test asserts the documented spelling matches the one the hook executes so the two cannot drift

### Full headline

a worker told to pay the whole suite locally reaches for `-n auto` and gets a RED tree that the push hook does not reproduce - MEASURED 2026-09-10 against a green tree: `python -m pytest tests -q -n auto` reported `3 failed, 6184 passed` exit 1, while `-n auto --dist loadfile` - the spelling `.githooks/pre-push` actually executes - reported `6187 passed` exit 0 over the same collection, and all three failures pass serially both in the lane worktree and in a clean worktree at the base commit, so the red is the scheduler and nothing else; the three are one hook-sandbox subprocess test and two same-file tests in `tests/save/test_properties.py` that the default scheduler splits across workers - the reasoning for `--dist loadfile` is recorded ONLY in the hook's own comments, and `tools/headless-queue.md` section 7a gives a whole-tree spelling with no `--dist` guidance at all

## CS-969

### Acceptance

an arm drives the negative-count branch of each reader with a planted non-empty value and asserts what the frame holds at that encoding, and the arm is shown load-bearing by a mutation that removes the branch rather than by its own greenness

### Full headline

`clockspeed/save/objects.py::_payload_text` and `clockspeed/save/objects.py::_Cursor.string` both carry a live negative-count UTF-16-LE branch that NO planted-marker arm in `tests/save/` drives, measured 2026-09-11 by reading the wide spelling back through both readers by hand - so the body-side wide path is exercised only by a probe run outside the suite, and `_payload_text` RETURNS None rather than raising on a decode failure, which means a wide payload string is read and not refused

## CS-974

### Acceptance

only a verdict on a stated ALLOWLIST rolls up as good, an arm sweeps every member of `CI_VERDICTS` and asserts the roll-up for each, and the arm is shown load-bearing by a mutation that widens the allowlist rather than by its own greenness

### Full headline

`ops/loop/queue_loop.py` decides a cycle's `ok` roll-up against `_CI_ROLLUP_BAD`, a DENYLIST of two verdicts, so `cancelled`, `skipped`, `timeout`, `unavailable` and `unknown` all roll up as GOOD - measured 2026-09-11 by sweeping `CI_VERDICTS` through the real `run_loop`: each of the five gives twelve cycles, `ok: true` on every row and exit 0, the same shape the file's own comment calls the defect, fixed for outcomes by the `PRODUCTIVE_OUTCOMES` allowlist and left standing one field over - NOTE the measured counter-reset half of this, where one transient `unavailable` extended a dead night from three cycles to six, was closed incidentally by CS-970's `03bcf1c` because the progress counter no longer reads the `ok` roll-up at all; what remains open is the roll-up itself, which still reports a cancelled, skipped, timed-out, unavailable or unknown CI verdict as a good cycle

## CS-975

### Acceptance

the launcher either waits for the driver and reports its exit code, or records the code where an operator reading the next morning will see it, with an arm driving a non-zero exit and asserting it is surfaced

### Full headline

nothing reads the `queue` driver's exit code, so every number it returns is decorative: `ops/loop/launch_queue_loop.ps1` starts the driver with `Start-Process` and no `-Wait`, then prints its started banner unconditionally, and a repo-wide sweep of `*.ps1`, `*.md`, `*.json` and `*.xml` finds no consumer of the process result - CS-970 added `EXIT_NO_PROGRESS` and `EXIT_UNKNOWN_STOP` specifically so a night that accomplished nothing could not report success, and both are observed by no one, so the driver's own promise that no launcher prints a success banner over a no-op holds only for the stop-sentinel pre-check

## CS-993

### Acceptance

two lanes cannot run a suite simultaneously, the second WAITS rather than failing, and a holder that dies releases rather than wedging the lane, proven by an arm where the second lane's suite step blocks until the first releases and by an arm where a killed holder leaves the ration acquirable

### Full headline

nothing rations the suite step across concurrent lanes, and the failure is already measured on this box rather than predicted: three projects' pytest runs at once reported `3402 passed, 1 error` while 2163 tests never ran, and two parallel xdist suites exhaust the Windows fork budget so the failures surface on unrelated subprocess tests and read as random flakes rather than as resource exhaustion, which means a parallel lane would report a green it did not earn

