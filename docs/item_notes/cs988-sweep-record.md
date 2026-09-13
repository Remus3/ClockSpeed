<!-- Annex to CS-988 in docs/item_notes/phase6.md. A DECLARED DEPARTURE from the
one-leaf-per-phase rule in docs/item_notes.md, recorded in the routing table there
and in docs/LEDGER.md rather than made silently. It is per-site MEASUREMENT DATA for
an OPEN item, not an item body, and it is not archived because docs/_archive/ is
excluded from search and sections 6 to 8 are the next action's direct input. -->

# CS-988 slice A - sweep record

MEASURED 2026-09-13 in worktree `agent-ad45630ce2d98d6dd` at base `b7b3e98`.
Scratch hand-back, NOT committed. Every number below was read off a run in this
worktree; nothing here is carried forward from a prior session's report.

## 1. The population

An AST scan over `tests/**/*.py` for every module-level assigned Name reachable
anywhere inside the `argvalues` expression of a `.parametrize(...)` call:

    PAIRS 193   FILES 49

That reproduces the 193/49 the brief states, independently derived.

## 2. The narrowing operator, and why it has two forms

One line, applied at the knob's own definition, shape-directed:

    RHS is a Tuple or List display with >= 2 elements  ->  (RHS)[:-1]
    otherwise (call, comprehension, name, concatenation) ->  (RHS)[:1]

The two forms are not a convenience. A hand-maintained literal's minimal
plausible edit is dropping a member; a derived population's is truncating it.
Calibration forced the split - see section 3.

Every mutation was proved to land by sha256 of the file bytes before and after,
and restored from the in-memory byte snapshot in a `finally`, never with
`git checkout`. `PYTHONDONTWRITEBYTECODE=1` throughout, so no pyc was written
and no same-second mutation could be served an earlier one's bytecode.

## 3. Calibration controls - all four reproduce

| site | recorded | this run | operator |
| --- | --- | --- | --- |
| DOCUMENTED_PATHS  tests/test_architecture_attributions.py | -54 | -54 | (RHS)[:2] |
| DOCUMENTED_PATHS  same site | - | -55 | (RHS)[:1] |
| DATA_MODULES  tests/data/test_phase2_gate.py | -6 | -6 | (RHS)[:-1], drops `version` |
| DATA_MODULES  same site | -5 | -5 (predicted, see below) | drops `locate` |
| CLOCKSPEED_PACKAGES  tests/test_scaffold.py | -9 | -9 | (RHS)[:2] |
| CLOCKSPEED_PACKAGES  same site | - | -10 | (RHS)[:1] |
| LEVEL_KEYS  tests/test_tier1_budget.py | -2 | -2 | (RHS)[:-1] |

**THE RECONCILIATION, and it is a finding about the prior record rather than
about the repo.** Under a one-element truncation the two DERIVED controls come
out at -55 and -10, exactly one arm deeper than the -54 and -9 on file. Under a
TWO-element truncation they are -54 and -9 exactly. So the narrowing the prior
pass applied to a derived knob kept TWO members, not one. Measured, not argued:
`[:2]` was run on both and printed those two numbers. The two LITERAL controls
match on the nose with no adjustment, which is what pins the split in the
operator. Neither population has drifted - `tests/test_scaffold.py` has two
commits in its whole history and neither is recent.

**THE -5 DATA_MODULES ARM IS THE ONE NUMBER HERE I DID NOT RUN.** `(RHS)[:-1]`
drops `version` and gives -6 across all six use sites; -5 is what dropping
`locate` gives, because the comprehension at line 271 already excludes it. That
is arithmetic over the six measured use sites, not a run. Treat it as
UNMEASURED by me and confirmed only by the prior record.

## 4. Leg 1 - collect-only, all 193

| verdict | pairs |
| --- | --- |
| DEFERRED | 9 |
| LEG1-PASS | 93 |
| NARROWING-INVALID | 48 |
| NO-REDUCTION | 43 |

- LEG1-PASS: the narrowing reduced the module's collected arm count.
- NO-REDUCTION: the narrowing applied cleanly and the count did not fall, so
  the criterion fails at leg 1 and the site is not an instance.
- NARROWING-INVALID: the knob is a Mapping, frozenset, Fraction or int, so the
  slice raised at import. NOT a verdict - these 48 are UNMEASURED, and a
  different operator might reduce their arm counts.
- DEFERRED: the 9 pairs in `tests/surface/test_aggregate_count_prose.py`, which
  is another slice's file this session. Untouched, unmeasured, unclassified.

## 5. Leg 2 - the guard population

The objector set was DERIVED per candidate, in two phases, and is stated with
every verdict:

- phase A: the candidate's own module, plus every runnable `tests/` module
  whose source names the CONSTANT as a whole word. 81 of 93 candidates have
  zero external name references.
- phase B: the eight modules MEASURED under a `sys.addaudithook` trace to OPEN
  all 143 `tests/*.py` sources - so each one reads the mutated bytes whatever
  the constant is called - plus every module naming the candidate's module path
  or stem.

      tests/test_liveness.py
      tests/test_docs_citations.py
      tests/test_toolpath.py
      tests/save/test_absolute_claims.py
      tests/save/test_oracle_citations.py
      tests/test_chained_cause_census.py
      tests/test_tier1_budget.py
      tests/test_scaffold.py

**THE WALKER SET IS MEASURED, NOT GREPPED, AND THE GREP WAS WRONG.** A regex
for a py-enumeration plus a tests root nominated 11 modules. The audit-hook
trace says six of those open 9 files or fewer - `tests/save/test_phase4_gate.py`
opens FIVE - while three modules the regex missed open all 143. Running the
regex set cost 250s per candidate and graded four modules that cannot see the
mutation at all.

## 6. CONFIRMED INSTANCES - green across the whole derived guard set

| delta | site | operator | guard modules |
| --- | --- | --- | --- |
| -55 | tests/test_architecture_attributions.py::DOCUMENTED_PATHS | ({RHS})[:1] | 9 |
| -36 | tests/save/test_independent_table.py::MEASURED_PAIRS | ({RHS})[:1] | 10 |
| -32 | tests/test_architecture_attributions.py::WITNESS_ROWS | ({RHS})[:1] | 9 |
| -31 | tests/test_architecture_attributions.py::TOPOLOGY | ({RHS})[:1] | 9 |
| -17 | tests/test_headless_queue_prompt.py::TOKENS | ({RHS})[:1] | 12 |
| -12 | tests/save/test_phase4_gate.py::SAVE_MODULES | ({RHS})[:1] | 11 |
| -10 | tests/test_hook_interpreter_ladder.py::HOOK_NAMES | ({RHS})[:-1] | 13 |
| -10 | tests/test_scaffold.py::CLOCKSPEED_PACKAGES | ({RHS})[:1] | 17 |
| -7 | tests/solve/test_phase3_gate.py::SOLVE_MODULES | ({RHS})[:1] | 10 |
| -6 | tests/data/test_phase2_gate.py::DATA_MODULES | ({RHS})[:-1] | 15 |
| -6 | tests/save/test_phase4_gate.py::_INJECTIONS | ({RHS})[:-1] | 11 |
| -5 | tests/save/test_world.py::_FAILURE_PARAMS | ({RHS})[:1] | 19 |
| -4 | tests/save/test_independent_table.py::_TRUNCATIONS | ({RHS})[:-1] | 10 |
| -4 | tests/save/test_properties.py::_FORCED_DISCOVERY_FAILURES | ({RHS})[:-1] | 27 |
| -4 | tests/solve/test_optimize.py::_SOURCE_FILES | ({RHS})[:-1] | 11 |
| -4 | tests/test_architecture_attributions.py::ATTRIBUTED_TOKENS | ({RHS})[:1] | 9 |
| -3 | tests/save/test_header.py::HEADER_VERSIONS | ({RHS})[:-1] | 15 |

Every one of these was green in phase A and green in phase B, exit code 0 read
off the process, never off a pipe.

### The second-derivation question, answered per instance

The only arm-count backstop in the repo is `_declared_case_count` in
`tests/surface/test_aggregate_count_prose.py`, and a repo-wide grep finds no
other module importing that file. So NO confirmed instance is graded by a
backstop today, let alone by an independent re-derivation.

Six instance modules do contain an equality or symmetric-difference arm
somewhere in the file. That shape is present but it is NOT wired to the knob
that moved - and the proof is the run itself: if it re-derived that population,
the narrowing would have reddened it, and it did not. So for all 17, the answer
is the same and it is measured rather than argued: **neither a second
derivation nor a backstop count grades any of them.**

## 7. DEFENDED - the narrowing reduced arms and something reddened

32 of 93, every one caught in phase A, and MEASURED: all 32 reddened only in the
candidate's OWN module - zero external reddening nodes across the whole set. No
DEFENDED verdict needed the walker set or an external name reference to reach
it, which is why phase A could settle them for a tenth of phase B's cost.

| delta | site | first reddening node |
| --- | --- | --- |
| -75 | tests/save/test_phase4_gate.py::READ_ONLY_SOURCES | tests/save/test_phase4_gate.py::test_the_writer_is_on_the_scanned_set_and_is_the_only_exemption |
| -21 | tests/save/test_phase4_gate.py::CORRUPTION_CASES | tests/save/test_phase4_gate.py::test_every_published_corruption_helper_is_exercised |
| -19 | tests/save/test_phase4_gate.py::SAVE_SOURCES | tests/save/test_phase4_gate.py::test_the_composer_imports_all_five |
| -15 | tests/save/test_phase4_gate.py::TRUNCATION_CASES | tests/save/test_phase4_gate.py::test_every_pinned_truncation_boundary_is_exercised |
| -10 | tests/solve/test_optimize.py::BOTH_BACKENDS | tests/solve/test_optimize.py::test_swapping_the_backend_changes_no_caller |
| -5 | tests/test_docs_citations.py::GUARDED_DOCS | tests/test_docs_citations.py::test_every_markdown_file_carrying_a_citation_is_guarded_or_recorded_unguarded |
| -4 | tests/save/test_chunks.py::_FILE_TRUNCATIONS | tests/save/test_chunks.py::test_the_corpus_still_carries_the_truncation_points_this_module_walks |
| -3 | tests/shell/test_shell_assets.py::REQUIRED_MAIN_WIRING | tests/shell/test_shell_assets.py::test_the_wiring_table_still_holds_every_seam_it_was_written_for |
| -3 | tests/solve/test_phase3_gate.py::SOLVE_SOURCES | tests/solve/test_phase3_gate.py::test_the_scanned_module_set_is_exactly_the_solve_package |
| -3 | tests/test_architecture_attributions.py::ATTRIBUTED | tests/test_architecture_attributions.py::test_the_manifest_names_no_section_the_document_lost |
| -3 | tests/test_chained_cause_census.py::_DEFERRED_SHAPES | tests/test_chained_cause_census.py::test_the_over_and_under_report_rows_are_both_populated |
| -3 | tests/test_headless_queue_prompt.py::RULES | tests/test_headless_queue_prompt.py::test_no_rule_can_be_narrowed_by_deleting_one_of_its_tokens |
| -2 | tests/save/test_header.py::_HEADER_SCOPE_CUTS | tests/save/test_header.py::test_the_truncation_matrix_is_fully_partitioned |
| -2 | tests/save/test_properties.py::_PROPERTY_READERS | tests/save/test_properties.py::test_the_frame_assertion_covers_every_exported_property_reader |
| -2 | tests/shell/test_shell_assets.py::FORBIDDEN_TLS_TOKENS | tests/shell/test_shell_assets.py::test_the_raw_token_sweep_catches_a_bypass_hidden_behind_a_regex_literal |
| -2 | tests/test_chained_cause_census.py::_CLONE_SHAPES | tests/test_chained_cause_census.py::test_each_leaking_refusal_is_refused_and_measured_to_leak[impostor_named_clone] |
| -2 | tests/test_chained_cause_census.py::_LIMIT_TEN_ESCAPES | tests/test_chained_cause_census.py::test_neither_refusal_population_is_empty_and_together_they_are_the_table |
| -2 | tests/test_commit_msg_gate.py::SHAPES | tests/test_commit_msg_gate.py::test_the_only_divergences_from_git_are_the_two_recorded_ones |
| -1 | tests/save/test_header.py::_CHUNK_SCOPE_CUTS | tests/save/test_header.py::test_the_truncation_matrix_is_fully_partitioned |
| -1 | tests/shell/test_shell_assets.py::MAIN_MODULE_BINDINGS | tests/shell/test_shell_assets.py::test_the_module_binding_table_covers_every_lib_main_requires |
| -1 | tests/shell/test_shell_assets.py::REQUIRED_CALL_ARGUMENTS | tests/shell/test_shell_assets.py::test_no_literal_answer_is_handed_to_a_supervisor_decision |
| -1 | tests/solve/test_phase3_gate.py::SOLVE_TEST_SOURCES | tests/solve/test_phase3_gate.py::test_the_scanned_solve_test_set_is_exactly_the_solve_test_package |
| -1 | tests/surface/test_server.py::TOKEN_SUBJECTS | tests/surface/test_server.py::test_every_token_the_asset_gate_declares_has_a_subject_that_grades_it |
| -1 | tests/surface/test_world.py::SITE_JUDGED_READS | tests/surface/test_world.py::test_a_site_judged_read_reaches_only_its_one_permitted_call[records-len] |
| -1 | tests/test_chained_cause_census.py::_CLEAN_REFUSALS | tests/test_chained_cause_census.py::test_neither_refusal_population_is_empty_and_together_they_are_the_table |
| -1 | tests/test_chained_cause_census.py::_CLEARED_SHAPES | tests/test_chained_cause_census.py::test_neither_refusal_population_is_empty_and_together_they_are_the_table |
| -1 | tests/test_chained_cause_census.py::_LEAKING_REFUSALS | tests/test_chained_cause_census.py::test_neither_refusal_population_is_empty_and_together_they_are_the_table |
| -1 | tests/test_report_redaction_classes.py::HOME_SPELLING_LABELS | tests/test_report_redaction_classes.py::test_the_graded_home_spelling_labels_are_the_ones_the_oracle_produces |
| -1 | tests/test_tier1_budget.py::EXPECTED_BOUND_NOUNS | tests/test_tier1_budget.py::test_the_bound_nouns_are_what_this_module_pins |
| -1 | tests/test_tier1_budget.py::EXPECTED_NARRATIVE_EXACT | tests/test_tier1_budget.py::test_the_exclusion_table_is_what_this_module_pins |
| -1 | tests/test_tier1_budget.py::EXPECTED_NARRATIVE_PREFIXES | tests/test_tier1_budget.py::test_the_exclusion_table_is_what_this_module_pins |
| -1 | tests/test_tier1_budget.py::EXPECTED_NUMBER_WORDS | tests/test_tier1_budget.py::test_the_number_words_are_what_this_module_pins |

## 8. INDETERMINATE - phase A green, phase B never run

44 candidates. Phase A passed; the walker set and the module-path citers were
never run against them because the sweep hit its wall clock. **These are NOT
instances and NOT defended. They are unmeasured at leg 2 and are deliberately
left unranked and unclassified.**

- -3  tests/save/test_properties.py::_FORCED_READ_FAILURES
- -2  tests/save/test_phase4_gate.py::LOADABLE_FIXTURES
- -2  tests/save/test_properties.py::_MAP_STATES
- -2  tests/shell/test_shell_assets.py::MAIN_SINGLETONS
- -2  tests/surface/test_server.py::TRAVERSALS
- -2  tests/test_architecture_attributions.py::NOT_BUILT_SECTIONS
- -2  tests/test_doc_budget.py::PLANT_SITES
- -2  tests/test_hook_interpreter_ladder.py::MESSAGE_CLASSES
- -2  tests/test_hook_interpreter_ladder.py::TRUNCATIONS
- -2  tests/test_pretooluse_gate.py::BROKEN_INPUTS
- -2  tests/test_tier1_budget.py::LEVEL_KEYS
- -1  tests/data/test_locate.py::ACCOUNT_DIR_SHAPES
- -1  tests/save/test_objects.py::_SUMMARY_NAME_LENGTHS
- -1  tests/save/test_phase4_gate.py::_SCANNER_NEGATIVES
- -1  tests/save/test_properties.py::_SUPPLIED_MAP_STATES
- -1  tests/save/test_world.py::_COMPLETE_REGISTRY_CODES
- -1  tests/save/test_world.py::_LOADABLE_FIXTURES
- -1  tests/save/test_world.py::_SURVIVING_SCHEMA_SUBJECTS
- -1  tests/save/test_world.py::_UNLOCK_SHAPES
- -1  tests/solve/test_phase3_gate.py::DOCS_EXTRACT_CARRIERS
- -1  tests/solve/test_phase3_gate.py::REGISTRY_CONSUMERS
- -1  tests/solve/test_phase3_gate.py::_DETECTOR_NEGATIVES
- -1  tests/solve/test_phase3_gate.py::_DETECTOR_POSITIVES
- -1  tests/solve/test_phase3_gate.py::_TOLERANCE_NEGATIVES
- -1  tests/solve/test_phase3_gate.py::_TOLERANCE_POSITIVES
- -1  tests/surface/test_contract.py::MALFORMED_BLOCKERS
- -1  tests/surface/test_contract.py::REFLECTED_PATHS
- -1  tests/surface/test_panel_solve.py::_EXIT_PATHS
- -1  tests/surface/test_pending_route_count.py::COUNT_WORDS
- -1  tests/test_architecture_attributions.py::NOT_BUILT_PACKAGES
- -1  tests/test_chained_cause.py::OSERROR_ROOTED_SITES
- -1  tests/test_chained_cause_census.py::_CALLEE_EXPECTATIONS
- -1  tests/test_chained_cause_census.py::_CHAIN_RULES
- -1  tests/test_chained_cause_census.py::_PLANTED_EXPECTATIONS
- -1  tests/test_chained_cause_census.py::_STRING_NAMED_ATTACHMENTS
- -1  tests/test_dated_headings.py::NOVEL_HEADINGS
- -1  tests/test_facts_probe.py::ACCOUNT_DIR_SHAPES
- -1  tests/test_hook_interpreter_ladder.py::ARGUMENT_IGNORING_PROGRAMS
- -1  tests/test_pretooluse_gate.py::PARITY_SAMPLES
- -1  tests/test_scaffold.py::DOC_OWNERSHIP_FILES
- -1  tests/test_scaffold.py::PACKAGE_TOPOLOGY
- -1  tests/test_scaffold.py::REQUIRED_DIRECTORIES
- -1  tests/test_tier1_budget.py::DURATION_SPELLINGS
- -1  tests/test_toolpath.py::UNROOTED_ENTRIES

## 9. UNMEASURED, stated as unmeasured

- The 48 NARROWING-INVALID pairs. A Mapping or frozenset knob needs an operator
  this sweep did not have. No verdict, no severity, no band.
- The 9 DEFERRED pairs in `tests/surface/test_aggregate_count_prose.py`.
- The 44 INDETERMINATE rows above.
- The -5 DATA_MODULES narrowing, arithmetic only.
- The 43 NO-REDUCTION pairs are measured at leg 1 and fail the criterion there;
  they were never taken to leg 2 because the criterion is conjunctive.

## 10. RE-MEASURE IN PRIMARY

**Every leg-2 verdict in this record carries this flag**, green and red alike.
No instance's arm COUNT depends on a filesystem or git walk - the deltas are
checkout-independent and stand. But the guard set includes
`tests/test_liveness.py` and `tests/test_docs_citations.py`, both of which
enumerate the tree, and a worktree carries no `moon_sync_inbox/`. A guard that
is green here can be red in the primary checkout for that reason alone.

## 11. Where I stopped

Leg 1: complete, 193 of 193.
Leg 2 phase A: complete, 93 of 93 leg-1 candidates.
Leg 2 phase B: 17 of 61 phase-A greens, taken in descending arm delta. The
boundary is exactly there: the last site measured is
`tests/save/test_header.py::HEADER_VERSIONS` at -3, and every phase-A green at
-3 or shallower that is not in section 6 is in section 8.
