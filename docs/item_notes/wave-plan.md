# Clockspeed - the wave plan, an annex

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**This file is an ANNEX to `docs/item_notes.md`, not a phase leaf.** It carries no item
section and no `## CS-nnn` heading, so `tools/drift_guard.py` guard (j) neither routes to
it nor reads a section out of it. It holds the wave table of the session 159 plan, one
row per slice, and pointers; every rule it depends on is owned elsewhere and named here.

**Pointers - each fact has one owner:**

- Each row's item line: `ROADMAP.md`.
- Each row's acceptance, wave id and its item's `Write-list:` field: its section in its leaf,
  found through the leaf table in `docs/item_notes.md`.
- The map from plan key to CS id, and each filing batch's record: `docs/LEDGER.md`.
- Conditional rows and their triggers: `BACKLOG.md`.
- Lane scopes: `config/lane_scopes.json`.
- Provenance rows for new tracked files: `tools/provenance.tsv`.
- The hand-off a cold session starts from: `CS-NEXT-SESSION.txt`.
- Each row's Write-list cell: `docs/item_notes/wave-plan-write-lists.md`, by its Slice cell.
- Each row's hub-chain place: its `chain` cell, keyed by `### Hub files` below; a leaf's
  `Hub chains` line is its filing-time per-wave order and is not read for a place.
- The wave runbook - wave size (B, G and the capacity cap), the one push and the exit record: `docs/OPERATIONS.md` section 10.8.
- The landing rule for each group's new files, its stamps and its census run: `docs/OPERATIONS.md` section 10.8, "10.8 Waves - one per session, one gated suite, one push", the Landing stamps paragraph; the stamp command: `docs/OPERATIONS.md` section 2.

Re-pack tools: <sidecars>/CS/plan-s159-tools/ - the five plan files of planning session 159, sha256 values in their docs/LEDGER.md copy record.

## Wave table

| Wave | Group | Slice | Item | Class | New files | Landing files | Hub text owed | Lane scope | Milestone | Entry conditions | chain |
|---|---|---|---|---|---|---|---|---|---|---|---|
| W0a | merger | W0a-M01 | U-158 not filed | process | none | `docs/item_notes/wave-plan.md` | none | - | - | - | - |
| W0a | merger | W0a-M02 | CS-1406 part 1 | process | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-850.md`, `docs/item_notes/phase4.md`, `docs/item_notes/phase7.md` | none | - | - | - | H052 1/8 |
| W0a | merger | W0a-M03 | CS-1406 part 2 | process | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups.md`, `docs/item_notes/phase4.md` | none | - | - | - | - |
| W0a | merger | W0a-M04 | CS-1406 part 3 | process | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-850.md`, `docs/item_notes/phase4-followups-900.md`, `docs/item_notes/phase4-followups.md` | none | - | - | - | - |
| W0a | merger | W0a-M05 | CS-1406 part 4 | process | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-1000.md`, `docs/item_notes/phase4-followups-960.md`, `docs/item_notes/phase6.md` | none | - | - | - | - |
| W0a | merger | W0a-M06 | CS-1406 part 5 | process | none | `BACKLOG.md`, `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md`, `docs/item_notes/phase7.md` | none | - | - | - | - |
| W0a | merger | W0a-M07 | CS-1406 part 6 | process | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase7.md` | none | - | - | - | - |
| W0a | merger | W0a-M08 | U-145 not filed | process | none | `CS-NEXT-SESSION.txt`, `docs/GATED.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W0b | merger | W0b-M01 | CS-1419 part 1 | process | none | `WAKEUP_NOTES.md` | none | - | - | - | - |
| W0b | merger | W0b-M02 | CS-1419 part 2 | process | none | `CS-NEXT-SESSION.txt`, `docs/LEDGER.md` | none | - | - | - | - |
| W0b | merger | W0b-M03 | CS-1409 part 1 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase7.md`, `docs/item_notes/wave-plan.md`, `tools/provenance.tsv` | none | - | - | - | - |
| W0b | merger | W0b-M04 | CS-1409 part 2 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase5.md` | none | - | - | - | - |
| W0b | merger | W0b-M05 | CS-1409 part 3 | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | none | - | - | - | - |
| W0b | merger | W0b-M06 | CS-1409 part 4 | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | none | - | - | - | - |
| W0b | merger | W0b-M07 | CS-1409 part 5 | process | none | `BACKLOG.md`, `docs/LEDGER.md`, `docs/item_notes/phase4-followups-960.md`, `docs/item_notes/phase5.md`, `docs/item_notes/phase6.md`, `docs/item_notes/phase7.md` | none | - | - | - | - |
| W0b | merger | W0b-M08 | CS-1409 part 6 | process | none | `CS-NEXT-SESSION.txt`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase7.md`, `docs/item_notes/wave-plan.md` | none | - | - | - | - |
| W0b | merger | W0b-M09 | CS-1412 | process | none | `docs/item_notes/wave-plan.md` | none | - | - | - | - |
| W0b | merger | W0b-M10 | CS-1413 | process | none | `CS-NEXT-SESSION.txt`, `docs/LEDGER.md` | none | - | - | - | - |
| W0b | merger | W0b-M11 | CS-1411 | process | none | `docs/LEDGER.md`, `docs/item_notes/wave-plan.md` | `docs/OPERATIONS.md` | - | - | - | - |
| W0b | merger | W0b-M12 | CS-1414 | process | none | `docs/item_notes/wave-plan.md` | `docs/OPERATIONS.md` | - | - | - | - |
| W0b | merger | W0b-M13 | CS-1415 | process | none | `docs/item_notes/wave-plan.md` | none | - | - | - | - |
| W0b | merger | W0b-M14 | CS-1417 | process | none | `CS-NEXT-SESSION.txt`, `config/lane_scopes.json`, `docs/item_notes/wave-plan.md` | `docs/OPERATIONS.md` | - | - | - | H020 1/13 |
| W0b | merger | W0b-M15 | CS-1418 | process | none | `docs/LEDGER.md` | none | - | - | - | - |
| W0b | merger | W0b-M16 | CS-1366 | process | none | `BACKLOG.md`, `CS-NEXT-SESSION.txt`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase7.md` | none | - | - | - | - |
| W0a | 1 | W0-G1-S1 | CS-913.1 | product | none | none | none | - | - | - | H014 1/16; H015 1/15 |
| W0a | 1 | W0-G1-S2 | CS-425; CS-448; CS-489; CS-492; CS-614; CS-701; CS-839; CS-840; CS-841; CS-842; CS-938; CS-941; CS-976; CS-981; CS-993; CS-1007; CS-1119; CS-1255; CS-1259; U-001 not filed; U-113 not filed; U-139 not filed; U-155 not filed | process; product | none | `BACKLOG.md`, `CS-NEXT-SESSION.txt`, `ROADMAP.md`, `config/lane_scopes.json`, `docs/GATED.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-1000.md`, `docs/item_notes/phase4-followups-900.md`, `docs/item_notes/phase4-followups-960.md`, `docs/item_notes/phase4-followups.md`, `docs/item_notes/phase4.md`, `docs/item_notes/phase6.md`, `docs/item_notes/phase7.md` | none | - | - | - | H001 1/45; H007 1/25; H011 1/20; H069 1/6; H071 1/6; H085 1/5; H105 1/4; H110 1/4; H112 1/4; H114 1/4 |
| W0a | 2 | W0-G2-S1 | CS-914 | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | - | H040 1/9; H044 1/8 |
| W0a | 2 | W0-G2-S2 | CS-1248.1 | product | `clockspeed/solve/` `quantity`; `tests/solve/` `test-quantity` | none | none | - | - | - | - |
| W1 | 1 | W1-G1-S1 | CS-1439 part 1 | process | `clockspeed/surface/web/` `panel_diagnostics`; `tests/surface/` `test-panel_diagnostics` | none | none | - | - | wave per its leaf | H003 1/31 |
| W1 | 1 | W1-G1-S2 | CS-1401 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md` | none | - | v0.3.0 | - | H013 1/17; H029 1/9; H036 1/9; H052 2/8; H079 1/5 |
| W1 | 2 | W1-G2-S1 | CS-1439 part 2 | process | none | none | none | - | - | wave per its leaf | H001 2/45; H003 2/31; H007 2/25; H012 1/19; H016 1/15 |
| W1 | 2 | W1-G2-S2 | CS-454.1 | product | none | none | none | - | - | - | H031 1/9; H038 1/9; H040 2/9 |
| W1 | 3 | W1-G3-S1 | CS-1261 | product | `docs/adr/` `0027-cs-1261-local-api-hardening` | none | none | - | - | - | H007 3/25; H012 2/19; H032 1/9; H050 1/8; H119 1/4 |
| W1 | 3 | W1-G3-S2 | CS-1410 | process | none | none | none | - | - | - | H043 1/8 |
| W1 | lane | W1-L01 | CS-887 | product | `tests/surface/` `test-exit_codes` | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md`, `tools/provenance.tsv` | `docs/OPERATIONS.md` | lane gap | - | - | H007 4/25; H012 3/19; H020 2/13; H021 1/12 |
| W2 | 1 | W2-G1-S1 | CS-1439 part 3 | process | none | none | none | - | - | - | H088 1/5; H089 1/5 |
| W2 | 1 | W2-G1-S2 | CS-936.1 | process | `tests/` `test-scrub_era_refs`; `tools/` `scrub_era_refs` | none | none | - | - | - | - |
| W2 | 2 | W2-G2-S1 | CS-1204 | product | none | none | none | - | v0.2.0 | - | H003 3/31; H009 1/21; H032 2/9; H033 1/9; H045 1/8; H062 1/7 |
| W2 | 2 | W2-G2-S2 | CS-454.2 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | - | - | - | H049 1/8 |
| W2 | 3 | W2-G3-S1 | CS-909 | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | - | H020 3/13 |
| W2 | 3 | W2-G3-S2 | CS-1243.4 | product | `docs/adr/` `NNNN-the-degraded-d1-siting-form` | `BACKLOG.md`, `docs/adr/README.md`, `docs/item_notes/phase5.md`, `tools/provenance.tsv` | `BOOTSTRAP.md` | - | - | - | - |
| W2 | filing | W2-F01 | CS-1048 extension unfiled | product | none | `docs/item_notes/phase5.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W3 | 1 | W3-G1-S1 | CS-619.1 | process | `shell/lib/` `persist`; `shell/test/` `persist.test` | `tools/provenance.tsv` | none | - | - | - | H002 1/37; H005 1/26 |
| W3 | 1 | W3-G1-S2 | CS-1438 | product | none | `ROADMAP.md`, `THIRD_PARTY.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | `docs/OPERATIONS.md` | - | v0.2.0 | - | - |
| W3 | 2 | W3-G2-S1 | CS-1437 part 1 | product | `tests/surface/` `test-admission` | none | none | - | - | - | H007 5/25; H012 4/19; H045 2/8 |
| W3 | 2 | W3-G2-S2 | CS-1440 part 1 | product | `tests/data/` `test-data_root` | none | none | - | v0.2.0 | - | H031 2/9; H038 2/9; H040 3/9; H044 2/8; H057 1/7; H060 1/7; H063 1/6 |
| W3 | 3 | W3-G3-S1 | CS-1436 part 1 | product | `tests/surface/` `test-web_palette` | `config/lane_scopes.json`, `tools/provenance.tsv` | none | - | - | - | H004 1/26 |
| W3 | 3 | W3-G3-S2 | CS-1048.1 | product | `clockspeed/advisor/` `annotations`; `tests/advisor/` `test-annotations` | none | none | - | - | extension filed by W2 | - |
| W3 | filing | W3-F01 | CS-1058 extension unfiled | product | none | `docs/item_notes/phase5.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W3 | filing | W3-F02 | CS-1058 child row unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase5.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W3 | lane | W3-L01 | CS-618 | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | lane gap | - | - | H020 4/13 |
| W4 | 1 | W4-G1-S1 | CS-1437 part 2 | product | none | none | none | - | - | - | H012 5/19; H032 3/9; H050 2/8 |
| W4 | 1 | W4-G1-S2 | CS-1434 part 1 | product | `tests/surface/` `test-views` | none | none | - | v0.3.0 | - | H001 3/45; H003 4/31; H004 2/26; H016 2/15; H071 2/6; H073 1/6; H084 1/5; H115 1/4 |
| W4 | 2 | W4-G2-S1 | CS-1437 part 3 | product | none | `docs/item_notes/phase6.md` | none | - | - | - | H012 6/19; H033 2/9 |
| W4 | 2 | W4-G2-S2 | CS-1440 part 2 | product | none | none | none | - | v0.2.0 | - | H021 2/12; H042 1/9 |
| W4 | 3 | W4-G3-S1 | CS-1048.2 | product | none | none | none | - | - | extension filed by W2 | H057 2/7; H063 2/6 |
| W4 | 3 | W4-G3-S2 | CS-1058.3 | product | none | none | none | - | - | extension filed by W3; child row filed by W3 | H014 2/16; H015 2/15 |
| W4 | filing | W4-F01 | U-077 unfiled | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W5 | 1 | W5-G1-S1 | CS-1434 part 2 | product | none | none | none | - | v0.3.0 | - | H001 4/45; H003 5/31; H004 3/26; H071 3/6; H073 2/6; H088 2/5; H089 2/5; H115 2/4 |
| W5 | 1 | W5-G1-S2 | CS-1440 part 3 | product | none | `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `tools/provenance.tsv` | `docs/OPERATIONS.md` | - | v0.2.0 | - | H098 1/4; H099 1/4 |
| W5 | 2 | W5-G2-S1 | CS-1435 part 1 | product | `scripts/` `make_icon`; `tests/` `test-make_icon`; `shell/lib/` `identity`; `shell/test/` `identity.test` | none | none | - | v0.2.0 | - | - |
| W5 | 2 | W5-G2-S2 | U-077.1 unfiled | process | none | `BACKLOG.md` | `docs/OPERATIONS.md` | - | - | filed by W4 | H001 5/45; H008 1/23 |
| W5 | 3 | W5-G3-S1 | CS-1058.4 | product | none | none | none | - | - | extension filed by W3; child row filed by W3 | H014 3/16; H015 3/15 |
| W5 | 3 | W5-G3-S2 | CS-1427 part 5 | product | none | none | none | - | - | - | H092 1/4 |
| W5 | filing | W5-F01 | U-060 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W5 | filing | W5-F02 | U-073 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W5 | filing | W5-F03 | U-115 parts 1 to 3 unfiled | product | none | `ROADMAP.md`, `docs/item_notes/phase7.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W6 | 1 | W6-G1-S1 | CS-1435 part 2 | product | none | none | none | - | v0.2.0 | - | H002 2/37; H005 2/26; H026 1/10; H035 1/9; H098 2/4; H099 2/4 |
| W6 | 1 | W6-G1-S2 | U-073.1 unfiled | product | `clockspeed/surface/web/` `panel_play`; `tests/surface/` `test-panel_play` | `tools/provenance.tsv` | none | - | v0.3.0 | filed by W5 | H001 6/45; H003 6/31; H007 6/25; H012 7/19; H016 3/15; H025 1/10; H028 1/10 |
| W6 | 2 | W6-G2-S1 | CS-1435 part 3 | product | none | none | `docs/OPERATIONS.md` | - | v0.2.0 | - | - |
| W6 | 2 | W6-G2-S2 | U-073.4 unfiled | product | none | `tools/provenance.tsv` | none | - | v0.3.0 | filed by W5 | H001 7/45; H003 7/31; H007 7/25; H012 8/19; H016 4/15; H025 2/10; H028 2/10 |
| W6 | 3 | W6-G3-S1 | U-060.1 unfiled | product | none | none | none | - | v0.2.0 | filed by W5 | H005 3/26; H047 1/8; H068 1/6 |
| W6 | 3 | W6-G3-S2 | U-115.1 unfiled | product | none | `docs/LEDGER.md` | none | - | v0.2.0 | filed by W5 | H053 1/8 |
| W6 | filing | W6-F01 | CS-1260 child row unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W6 | lane | W6-L01 | CS-1067 | product | none | none | none | lane gap | - | - | - |
| W7 | 1 | W7-G1-S1 | U-073.2 unfiled | product | none | none | none | - | v0.3.0 | filed by W5 | H001 8/45; H004 4/26; H025 3/10; H028 3/10 |
| W7 | 1 | W7-G1-S2 | U-060.2 unfiled | product | none | none | none | - | v0.2.0 | filed by W5 | H047 2/8; H068 2/6 |
| W7 | 2 | W7-G2-S1 | CS-1260.1 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | none | - | - | child row filed by W6 | H001 9/45; H004 5/26 |
| W7 | 2 | W7-G2-S2 | CS-1252.1 | product | `clockspeed/audit/` `freshness`; `tests/audit/` `test-freshness`; `tests/surface/` `test-freshness` | none | none | - | v0.3.0 | - | H009 2/21; H013 2/17; H032 4/9; H036 2/9; H050 3/8; H054 1/7; H078 1/5; H091 1/4 |
| W7 | 3 | W7-G3-S1 | U-073.3 unfiled | product | none | `BACKLOG.md` | none | - | v0.3.0 | filed by W5 | H001 10/45; H073 3/6 |
| W7 | 3 | W7-G3-S2 | CS-623 | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | - | H002 3/37; H026 2/10; H046 1/8; H047 3/8 |
| W7 | filing | W7-F01 | U-061 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W7 | filing | W7-F02 | U-116 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W7 | filing | W7-F03 | U-117 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W8 | 1 | W8-G1-S1 | U-116 unfiled | product | `tests/surface/` `test-registry_provider_memo` | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | filed by W7 | H009 3/21; H021 3/12; H053 2/8; H087 1/5 |
| W8 | 1 | W8-G1-S2 | CS-1260.2 | product | none | none | none | - | - | child row filed by W6 | H001 11/45; H004 6/26; H006 1/26; H111 1/4 |
| W8 | 2 | W8-G2-S1 | U-117 unfiled | product | `clockspeed/surface/` `priority`; `tests/surface/` `test-priority` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | `docs/OPERATIONS.md` | - | - | filed by W7 | H021 4/12; H042 2/9; H087 2/5 |
| W8 | 2 | W8-G2-S2 | U-060.3 unfiled | product | none | none | none | - | v0.2.0 | filed by W5 | H002 4/37; H005 4/26 |
| W8 | 3 | W8-G3-S1 | U-060.4 unfiled | product | none | none | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W5 | - |
| W8 | 3 | W8-G3-S2 | U-061.1 unfiled | product | none | none | none | - | v0.2.0 | filed by W7 | H060 2/7; H120 1/4 |
| W8 | filing | W8-F01 | U-074 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W8 | filing | W8-F02 | U-097 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W9 | 1 | W9-G1-S1 | CS-1252.2 | product | none | none | none | - | v0.3.0 | - | H018 1/13; H024 1/11; H045 3/8; H062 2/7; H093 1/4; H094 1/4; H110 2/4; H113 1/4; H114 2/4 |
| W9 | 1 | W9-G1-S2 | U-074.1 unfiled | product | `tests/surface/` `test-panel_repaint` | `tools/provenance.tsv` | none | - | v0.3.0 | filed by W8 | H001 12/45; H003 8/31; H084 2/5; H085 2/5 |
| W9 | 2 | W9-G2-S1 | U-115.2 unfiled | product | `tests/surface/` `test-world_provider_reload` | none | none | - | v0.2.0 | filed by W5 | H009 4/21 |
| W9 | 2 | W9-G2-S2 | U-097.1 unfiled | product | `shell/lib/` `guard`; `shell/test/` `guard.test` | `tools/provenance.tsv` | none | - | - | filed by W8 | H002 5/37 |
| W9 | 3 | W9-G3-S1 | CS-622 | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | - | H002 6/37 |
| W9 | 3 | W9-G3-S2 | CS-1130.1 | process | none | none | none | - | - | - | H090 1/5 |
| W9 | filing | W9-F01 | CS-1251 extension unfiled | product | none | `docs/item_notes/phase5.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W10 | 1 | W10-G1-S1 | CS-1251.1 | product | `tests/save/` `test-settle` | `tools/provenance.tsv` | none | - | v0.3.0 | extension filed by W9 | H040 4/9; H044 3/8 |
| W10 | 1 | W10-G1-S2 | CS-1252.3 | product | none | none | none | - | v0.3.0 | - | H003 9/31; H004 7/26; H006 2/26; H010 1/21; H016 5/15; H047 4/8; H068 3/6; H086 1/5; H095 1/4 |
| W10 | 2 | W10-G2-S1 | U-074.2 unfiled | product | none | none | none | - | v0.3.0 | filed by W8 | H003 10/31; H085 3/5 |
| W10 | 2 | W10-G2-S2 | U-115.3 unfiled | product | `tests/surface/` `test-health_readiness` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase7.md` | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W5 | H009 5/21; H021 5/12; H033 3/9; H045 4/8; H062 3/7; H116 1/4 |
| W10 | 3 | W10-G3-S1 | CS-621 | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | - | H002 7/37 |
| W10 | 3 | W10-G3-S2 | CS-1151 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4-followups-1000.md`, `docs/item_notes/phase4-followups.md` | none | - | - | - | H011 2/20 |
| W11 | 1 | W11-G1-S1 | U-097.2 unfiled | product | none | none | none | - | - | filed by W8 | H002 8/37; H005 5/26 |
| W11 | 1 | W11-G1-S2 | CS-1251.2 | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md` | none | - | v0.3.0 | extension filed by W9 | H009 6/21; H015 4/15; H020 5/13; H116 2/4 |
| W11 | 2 | W11-G2-S1 | CS-1252.4 | product | none | `ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/item_notes/phase5.md`, `tools/provenance.tsv` | none | - | v0.3.0 | - | H001 13/45; H008 2/23; H017 1/15; H023 1/11; H041 1/9; H059 1/7; H071 4/6; H072 1/6 |
| W11 | 2 | W11-G2-S2 | U-074.3 unfiled | product | none | none | none | - | v0.3.0 | filed by W8 | H003 11/31; H025 4/10; H028 4/10; H084 3/5 |
| W11 | 3 | W11-G3-S1 | U-097.3 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | none | - | - | filed by W8 | - |
| W11 | 3 | W11-G3-S2 | CS-607 | process | none | none | none | - | - | - | - |
| W11 | filing | W11-F01 | U-059 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W11 | filing | W11-F02 | U-098 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W11 | filing | W11-F03 | U-115 part 4 unfiled | product | none | `ROADMAP.md`, `docs/item_notes/phase7.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W12 | 1 | W12-G1-S1 | U-115.4 unfiled | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase7.md` | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W11 | H009 7/21; H021 6/12; H033 4/9; H045 5/8; H062 4/7; H116 3/4 |
| W12 | 1 | W12-G1-S2 | U-061.2 unfiled | product | none | none | none | - | v0.2.0 | filed by W7 | H002 9/37; H005 6/26; H120 2/4 |
| W12 | 2 | W12-G2-S1 | CS-1432 part 1 | product | none | `docs/LEDGER.md` | none | - | v0.3.0 | - | H053 3/8 |
| W12 | 2 | W12-G2-S2 | U-098.1 unfiled | product | none | none | none | - | - | filed by W11 | H026 3/10; H035 2/9 |
| W12 | 3 | W12-G3-S1 | U-098.2 unfiled | product | none | none | none | - | - | filed by W11 | - |
| W12 | 3 | W12-G3-S2 | U-059.1 unfiled | product | `clockspeed/surface/` `owner`; `tests/surface/` `test-owner` | `tools/provenance.tsv` | none | - | - | filed by W11 | H007 8/25; H021 7/12; H042 3/9 |
| W12 | filing | W12-F01 | U-101 unfiled | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W12 | filing | W12-F02 | U-119 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W13 | 1 | W13-G1-S1 | CS-1432 part 2 | product | `clockspeed/surface/` `watch`; `tests/surface/` `test-watch` | none | none | - | v0.3.0 | - | - |
| W13 | 1 | W13-G1-S2 | U-119 unfiled | product | `tests/surface/` `test-start_purge` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | `docs/OPERATIONS.md` | - | - | filed by W12 | H014 4/16; H015 5/15; H021 8/12; H040 5/9; H044 4/8; H069 2/6 |
| W13 | 2 | W13-G2-S1 | CS-1432 part 3 | product | `clockspeed/surface/api/` `events`; `tests/surface/` `test-events` | none | none | - | v0.3.0 | - | H007 9/25; H012 9/19 |
| W13 | 2 | W13-G2-S2 | U-101.1 unfiled | process | `config/` `runtime_pins`; `tests/` `test-runtime_pins` | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W12 | H076 1/5; H122 1/4 |
| W13 | 3 | W13-G3-S1 | CS-1432 part 4 | product | none | none | none | - | v0.3.0 | - | H021 9/12 |
| W13 | 3 | W13-G3-S2 | CS-1142 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-1000.md` | none | - | - | - | H052 3/8 |
| W13 | filing | W13-F01 | U-002 unfiled | process | none | `ROADMAP.md`, `docs/item_notes/phase7.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W13 | filing | W13-F02 | U-091 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W13 | filing | W13-F03 | CS-1258 extension unfiled | product | none | `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W13 | lane | W13-L01 | CS-603 | process | none | none | none | lane gap | - | - | - |
| W14 | 1 | W14-G1-S1 | U-098.3 unfiled | product | none | none | none | - | - | filed by W11 | H002 10/37; H005 7/26 |
| W14 | 1 | W14-G1-S2 | U-002.1 unfiled | process | `installer/__init__`; `installer/manifest`; `tests/` `installer/test-manifest`; `tools/` `release_build`; `tests/` `packaging/test-release_build`; `tests/` `installer/__init__`; `tests/` `packaging/__init__` | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W13 | H077 1/5; H103 1/4 |
| W14 | 2 | W14-G2-S1 | U-091.1 unfiled | product | none | none | none | - | v0.2.0 | filed by W13 | H119 2/4 |
| W14 | 2 | W14-G2-S2 | U-098.4 unfiled | product | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | `docs/OPERATIONS.md` | - | - | filed by W11 | H002 11/37; H005 8/26; H026 4/10; H035 3/9 |
| W14 | 3 | W14-G3-S1 | U-098.5 unfiled | product | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | `docs/OPERATIONS.md` | - | - | filed by W11 | H002 12/37; H005 9/26; H026 5/10; H035 4/9 |
| W14 | 3 | W14-G3-S2 | CS-1258.1 | product | none | none | none | - | - | extension filed by W13 | H001 14/45; H004 8/26 |
| W15 | 1 | W15-G1-S1 | CS-1432 part 5 | product | `tests/surface/` `test-freshness_strip` | none | none | - | v0.3.0 | - | H001 15/45; H003 12/31; H004 9/26; H016 6/15 |
| W15 | 1 | W15-G1-S2 | U-002.2 unfiled | process | `tests/` `packaging/test-artifact_contents`; `tests/` `packaging/test-artifact_boot` | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W13 | H077 2/5 |
| W15 | 2 | W15-G2-S1 | U-091.2 unfiled | product | `shell/lib/` `mint`; `shell/test/` `mint.test` | none | none | - | v0.2.0 | filed by W13 | H002 13/37; H005 10/26; H046 2/8; H055 1/7 |
| W15 | 2 | W15-G2-S2 | U-101.2 unfiled | process | `tools/` `runtime_pins` | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W12 | H122 2/4 |
| W15 | 3 | W15-G3-S1 | U-002.3 unfiled | process | `tests/` `test-version_owner` | `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `tools/provenance.tsv` | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W13 | - |
| W15 | 3 | W15-G3-S2 | CS-608 | process | none | none | none | - | - | - | H001 16/45 |
| W15 | filing | W15-F01 | U-102 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W16 | 1 | W16-G1-S1 | CS-619.2 | process | none | none | none | - | - | - | H002 14/37; H005 11/26; H046 3/8; H055 2/7 |
| W16 | 1 | W16-G1-S2 | CS-1432 part 6 | product | none | none | none | - | v0.3.0 | - | H001 17/45; H003 13/31; H004 10/26; H006 3/26; H010 2/21; H016 7/15; H025 5/10; H028 5/10 |
| W16 | 2 | W16-G2-S1 | U-091.3 unfiled | product | `docs/adr/` `NNNN-certificate-lifecycle-and-the-per-start-token` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/adr/README.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W13 | H043 2/8; H121 1/4 |
| W16 | 2 | W16-G2-S2 | U-101.3 unfiled | process | `docs/adr/` `NNNN-runtime-pins` | `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/adr/README.md`, `tools/provenance.tsv` | none | - | v0.2.0 | filed by W12 | H076 2/5; H122 3/4 |
| W16 | 3 | W16-G3-S1 | U-102.1 unfiled | product | `installer/__main__`; `installer/cli`; `tests/` `installer/test-cli` | `docs/LEDGER.md`, `tools/provenance.tsv` | none | - | v0.2.0 | filed by W15 | H034 1/9; H076 3/5; H077 3/5; H103 2/4 |
| W16 | 3 | W16-G3-S2 | CS-1258.2 | product | none | none | none | - | - | extension filed by W13 | H001 18/45; H003 14/31; H016 8/15; H088 3/5; H089 3/5 |
| W16 | filing | W16-F01 | U-099 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W16 | lane | W16-L01 | CS-468 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | lane gap | - | - | H038 3/9 |
| W17 | 1 | W17-G1-S1 | CS-619.3 | process | `shell/lib/` `wiring`; `shell/test/` `wiring.test` | `tools/provenance.tsv` | none | - | - | - | H002 15/37; H005 12/26 |
| W17 | 1 | W17-G1-S2 | CS-1432 part 7 | product | `tests/surface/` `test-event_focus` | `docs/LEDGER.md` | `docs/hud_doctrine.md` | - | v0.3.0 | - | H001 19/45; H003 15/31 |
| W17 | 2 | W17-G2-S1 | CS-619.4 | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | - | - |
| W17 | 2 | W17-G2-S2 | CS-1432 part 8 | product | none | `ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md`, `docs/item_notes/phase6.md` | none | - | v0.3.0 | - | H043 3/8 |
| W17 | 3 | W17-G3-S1 | U-099.1 unfiled | product | `installer/fuses`; `tests/` `installer/test-fuses` | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W16 | - |
| W17 | 3 | W17-G3-S2 | U-102.7 unfiled | product | none | `docs/LEDGER.md`, `tools/provenance.tsv` | none | - | v0.2.0 | filed by W15 | H034 2/9; H076 4/5; H077 4/5; H103 3/4 |
| W18 | 1 | W18-G1-S1 | U-159 not filed | product | none | none | none | - | - | - | - |
| W18 | 1 | W18-G1-S2 | U-099.2 unfiled | product | none | none | none | - | v0.2.0 | filed by W16 | - |
| W18 | 2 | W18-G2-S1 | U-102.2 unfiled | product | `installer/paths`; `tests/` `installer/test-paths`; `installer/marker`; `tests/` `installer/test-marker` | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W15 | - |
| W18 | 2 | W18-G2-S2 | U-059.2 unfiled | product | none | none | none | - | - | filed by W11 | H002 16/37; H005 13/26; H046 4/8; H055 3/7 |
| W18 | 3 | W18-G3-S1 | CS-612 | process | none | none | none | - | - | - | H119 3/4 |
| W18 | 3 | W18-G3-S2 | CS-464 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | - | - | - | - |
| W19 | 1 | W19-G1-S1 | U-102.3 unfiled | product | `installer/runtimes`; `tests/` `installer/test-runtimes`; `installer/engine`; `tests/` `installer/test-engine` | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W15 | H034 3/9; H067 1/6 |
| W19 | 1 | W19-G1-S2 | U-059.3 unfiled | product | `tests/shell/` `test-owner_pipe` | `tools/provenance.tsv` | none | - | - | filed by W11 | - |
| W19 | 2 | W19-G2-S1 | U-102.4 unfiled | product | `installer/selftest`; `tests/` `installer/test-selftest`; `installer/report`; `tests/` `installer/test-report` | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W15 | H034 4/9; H067 2/6 |
| W19 | 2 | W19-G2-S2 | U-059.4 unfiled | product | `docs/adr/` `NNNN-the-shell-supervises-for-the-whole-session` | `docs/adr/README.md`, `tools/provenance.tsv` | `docs/OPERATIONS.md` | - | - | filed by W11 | - |
| W19 | 3 | W19-G3-S1 | CS-876 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-850.md` | none | - | - | - | H039 1/9 |
| W19 | 3 | W19-G3-S2 | CS-457 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | - | - | - | H011 3/20 |
| W19 | filing | W19-F01 | U-062 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W19 | filing | W19-F02 | U-134 unfiled | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W19 | filing | W19-F03 | U-149 unfiled | process | none | `ROADMAP.md`, `docs/item_notes/phase7.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W20 | 1 | W20-G1-S1 | U-134 unfiled | process | `tools/` `release_notes`; `tests/` `test-release_notes` | `BACKLOG.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `tools/provenance.tsv` | none | - | v0.2.0 | filed by W19 | - |
| W20 | 1 | W20-G1-S2 | U-102.5 unfiled | product | `installer/bootstrap/install`; `installer/bootstrap/install`; `installer/bootstrap/mint`; `installer/mint`; `tests/` `installer/test-mint`; `tests/` `installer/test-bootstrap_text` | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W15 | H034 5/9; H067 3/6 |
| W20 | 2 | W20-G2-S1 | U-102.8 unfiled | product | none | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W15 | H034 6/9; H067 4/6 |
| W20 | 2 | W20-G2-S2 | U-062.1 unfiled | product | none | none | none | - | v0.2.0 | filed by W19 | H046 5/8; H047 5/8; H055 4/7; H068 4/6 |
| W20 | 3 | W20-G3-S1 | CS-1436 part 2 | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | - | - |
| W20 | 3 | W20-G3-S2 | CS-1430 | product | `clockspeed/progress/` `delta`; `tests/progress/` `test-delta` | `docs/ARCHITECTURE.md`, `tools/provenance.tsv` | none | - | - | - | - |
| W20 | filing | W20-F01 | U-125 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W20 | filing | W20-F02 | U-132 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W20 | filing | W20-F03 | CS-1398 extension unfiled | product | none | `docs/item_notes/phase5.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W20 | lane | W20-L01 | CS-808 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups.md` | none | lane gap | - | - | H049 2/8; H104 1/4 |
| W21 | 1 | W21-G1-S1 | U-102.6 unfiled | product | `docs/adr/` `NNNN-the-installer` | `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/adr/README.md`, `tools/provenance.tsv` | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W15 | H043 4/8; H121 2/4 |
| W21 | 1 | W21-G1-S2 | CS-1248.2 | product | none | none | none | - | - | - | - |
| W21 | 2 | W21-G2-S1 | U-132.1 unfiled | product | `shell/lib/` `launch`; `shell/test/` `launch.test`; `shell/` `launcher/main` | none | none | - | v0.2.0 | filed by W20 | H002 17/37 |
| W21 | 2 | W21-G2-S2 | CS-1398.1 | product | none | `config/lane_scopes.json`, `docs/item_notes/phase5.md` | none | - | - | extension filed by W20 | H029 2/9; H075 1/5; H079 2/5; H080 1/5 |
| W21 | 3 | W21-G3-S1 | U-125.1 unfiled | product | `clockspeed/surface/` `oplog`; `tests/surface/` `test-oplog` | `tools/provenance.tsv` | none | - | - | filed by W20 | H007 10/25; H096 1/4 |
| W21 | 3 | W21-G3-S2 | CS-916.1 | product | none | none | none | - | - | - | H086 2/5; H092 2/4 |
| W22 | 1 | W22-G1-S1 | U-132.2 unfiled | product | `shell/` `launcher/package` | none | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W20 | H002 18/37; H046 6/8; H055 5/7 |
| W22 | 1 | W22-G1-S2 | U-062.2 unfiled | product | `shell/lib/` `lifecycle`; `shell/test/` `lifecycle.test` | none | none | - | v0.2.0 | filed by W19 | - |
| W22 | 2 | W22-G2-S1 | U-132.3 unfiled | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | v0.2.0 | filed by W20 | H002 19/37; H005 14/26; H067 5/6 |
| W22 | 2 | W22-G2-S2 | CS-1248.3 | product | none | none | none | - | - | - | H032 5/9; H050 4/8; H075 2/5 |
| W22 | 3 | W22-G3-S1 | U-099.3 unfiled | product | none | `BACKLOG.md`, `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | `docs/OPERATIONS.md` | - | - | filed by W16 | H002 20/37 |
| W22 | 3 | W22-G3-S2 | CS-609 | process | none | none | none | - | - | - | H061 1/7 |
| W22 | filing | W22-F01 | U-133 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W23 | 1 | W23-G1-S1 | U-133.1 unfiled | product | `installer/shellint`; `tests/` `installer/test-shellint`; `installer/procs`; `tests/` `installer/test-procs` | none | none | - | v0.2.0 | filed by W22 | - |
| W23 | 1 | W23-G1-S2 | U-062.3 unfiled | product | none | `docs/adr/README.md` | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W19 | H002 21/37; H005 15/26; H046 7/8; H053 4/8; H055 6/7 |
| W23 | 2 | W23-G2-S1 | U-133.2 unfiled | product | `installer/uninstall`; `tests/` `installer/test-uninstall`; `installer/recycle` | none | none | - | v0.2.0 | filed by W22 | - |
| W23 | 2 | W23-G2-S2 | CS-1046.1 | product | `clockspeed/surface/api/` `audit`; `tests/surface/` `test-audit`; `clockspeed/surface/api/` `plan`; `tests/surface/` `test-plan` | `tools/provenance.tsv` | none | - | v0.4.0 | - | H017 2/15 |
| W23 | 3 | W23-G3-S1 | CS-611 | process | none | `docs/item_notes/phase6.md` | none | - | - | - | H007 11/25; H012 10/19 |
| W23 | 3 | W23-G3-S2 | CS-620 | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | `docs/OPERATIONS.md` | - | - | - | H043 5/8 |
| W23 | filing | W23-F01 | U-126 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W23 | lane | W23-L01 | CS-465 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | lane gap | - | - | H048 1/8 |
| W24 | 1 | W24-G1-S1 | CS-1248.4 | product | none | none | none | - | - | - | H094 2/4; H113 2/4; H114 3/4 |
| W24 | 1 | W24-G1-S2 | U-126 unfiled | product | none | none | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W23 | H002 22/37; H005 16/26; H046 8/8; H047 6/8; H055 7/7 |
| W24 | 2 | W24-G2-S1 | U-133.3 unfiled | product | none | `docs/LEDGER.md` | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W22 | H034 7/9; H077 5/5; H103 4/4; H120 3/4 |
| W24 | 2 | W24-G2-S2 | CS-1046.2 | product | none | none | none | - | v0.4.0 | - | H001 20/45; H008 3/23; H032 6/9; H033 5/9; H042 4/9; H050 5/8; H051 1/8; H061 2/7 |
| W24 | 3 | W24-G3-S1 | CS-1046.3 | product | none | none | none | - | v0.4.0 | - | H009 8/21 |
| W24 | 3 | W24-G3-S2 | CS-915 | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | - | H001 21/45; H008 4/23 |
| W24 | filing | W24-F01 | U-004 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W25 | 1 | W25-G1-S1 | CS-1248.5 | product | none | none | none | - | - | - | H018 2/13; H027 1/10; H065 1/6 |
| W25 | 1 | W25-G1-S2 | U-004.1 unfiled | product | `installer/update`; `tests/` `installer/test-update`; `installer/net`; `tests/` `packaging/test-update_requests` | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W24 | - |
| W25 | 2 | W25-G2-S1 | CS-1248.6 | product | none | none | none | - | - | - | H097 1/4 |
| W25 | 2 | W25-G2-S2 | U-004.2 unfiled | product | none | none | none | - | v0.2.0 | filed by W24 | H034 8/9; H067 6/6 |
| W25 | 3 | W25-G3-S1 | CS-1046.4 | product | none | `ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | v0.4.0 | - | H020 6/13; H043 6/8 |
| W25 | 3 | W25-G3-S2 | CS-467 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | - | - | - | H014 5/16 |
| W25 | filing | W25-F01 | U-104 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W25 | filing | W25-F02 | U-118 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W26 | 1 | W26-G1-S1 | CS-1065 | product | none | none | none | - | - | - | H008 5/23; H020 7/13; H094 3/4; H097 2/4; H112 2/4; H113 3/4 |
| W26 | 1 | W26-G1-S2 | CS-1248.7 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md`, `tools/provenance.tsv` | none | - | - | - | H010 3/21 |
| W26 | 2 | W26-G2-S1 | U-004.3 unfiled | product | none | `docs/LEDGER.md` | none | - | v0.2.0 | filed by W24 | H002 23/37; H005 17/26; H043 7/8; H047 7/8; H068 5/6 |
| W26 | 2 | W26-G2-S2 | CS-1256.1 | product | none | none | none | - | - | - | H027 2/10; H032 7/9; H050 6/8; H065 2/6; H094 4/4; H113 4/4; H114 4/4 |
| W26 | 3 | W26-G3-S1 | U-104 unfiled | product | none | `docs/GATED.md`, `docs/LEDGER.md` | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W25 | H043 8/8; H121 3/4 |
| W26 | 3 | W26-G3-S2 | U-118.1 unfiled | product | `tests/advisor/` `test-advise_memo` | `ROADMAP.md`, `docs/item_notes/phase6.md`, `tools/provenance.tsv` | none | - | - | filed by W25 | H013 3/17; H036 3/9 |
| W26 | filing | W26-F01 | U-135 unfiled | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W26 | filing | W26-F02 | U-136 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W26 | lane | W26-L01 | CS-483 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4.md` | none | lane gap | - | - | H105 2/4 |
| W27 | 1 | W27-G1-S1 | U-135.1 unfiled | process | `tools/` `release_stage`; `tests/` `test-release_stage` | none | none | - | v0.2.0 | filed by W26 | - |
| W27 | 1 | W27-G1-S2 | CS-1256.2 | product | none | none | none | - | - | - | H018 3/13; H085 4/5; H086 3/5; H093 2/4; H095 2/4 |
| W27 | 2 | W27-G2-S1 | U-135.2 unfiled | process | `.github/workflows/` `release`; `tests/` `test-release_workflow` | none | none | - | v0.2.0 | filed by W26 | - |
| W27 | 2 | W27-G2-S2 | U-136.1 unfiled | product | `installer/migrate`; `tests/` `installer/test-migrate` | none | none | - | v0.2.0 | filed by W26 | H034 9/9 |
| W27 | 3 | W27-G3-S1 | U-135.3 unfiled | process | none | none | none | - | v0.2.0 | filed by W26 | - |
| W27 | 3 | W27-G3-S2 | U-136.2 unfiled | product | `tests/` `installer/test-first_run` | `docs/LEDGER.md` | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W26 | - |
| W27 | filing | W27-F01 | U-103 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W28 | 1 | W28-G1-S1 | U-118.2 unfiled | product | none | none | none | - | - | filed by W25 | H009 9/21; H017 3/15 |
| W28 | 1 | W28-G1-S2 | CS-1256.3 | product | `tests/surface/` `test-numeric_schema` | none | none | - | - | - | H006 4/26; H010 4/21; H066 1/6; H083 1/5; H097 3/4; H112 3/4 |
| W28 | 2 | W28-G2-S1 | U-103 unfiled | product | none | `THIRD_PARTY.md`, `docs/LEDGER.md` | none | - | v0.2.0 | filed by W27 | H076 5/5; H122 4/4 |
| W28 | 2 | W28-G2-S2 | U-118.3 unfiled | product | none | none | none | - | - | filed by W25 | H013 4/17; H017 4/15 |
| W28 | 3 | W28-G3-S1 | CS-1256.4 | product | none | `tools/provenance.tsv` | none | - | - | - | H008 6/23; H023 2/11 |
| W28 | 3 | W28-G3-S2 | U-118.4 unfiled | product | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | none | - | - | filed by W25 | H053 5/8 |
| W28 | filing | W28-F01 | CS-1257 extension unfiled | product | none | `ROADMAP.md`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W29 | 1 | W29-G1-S1 | CS-1420 part 1 | product | none | none | none | - | - | - | H086 4/5; H092 3/4 |
| W29 | 1 | W29-G1-S2 | CS-1257.1 | product | none | `docs/LEDGER.md` | none | - | v0.3.0 | extension filed by W28 | H057 3/7; H063 3/6 |
| W29 | 2 | W29-G2-S1 | CS-1420 part 2 | product | `clockspeed/solve/` `staging`; `tests/solve/` `test-staging` | none | none | - | - | - | H107 1/4 |
| W29 | 2 | W29-G2-S2 | CS-1257.2 | product | `tests/advisor/` `test-standing_statement` | none | none | - | v0.3.0 | extension filed by W28 | H013 5/17 |
| W29 | 3 | W29-G3-S1 | CS-1420 part 3 | product | none | none | none | - | - | - | - |
| W29 | 3 | W29-G3-S2 | CS-1257.3 | product | none | none | none | - | v0.3.0 | extension filed by W28 | H009 10/21; H017 5/15; H018 4/13; H024 2/11; H072 2/6 |
| W29 | filing | W29-F01 | CS-962 child row unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase4-followups-960.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W30 | 1 | W30-G1-S1 | CS-1420 part 4 | product | none | none | none | - | - | - | H075 3/5; H080 2/5 |
| W30 | 1 | W30-G1-S2 | CS-962.1 | product | none | none | none | - | v0.3.0 | child row filed by W29 | H001 22/45; H004 11/26 |
| W30 | 2 | W30-G2-S1 | CS-1257.4 | product | none | none | none | - | v0.3.0 | extension filed by W28 | H001 23/45; H003 16/31; H006 5/26; H010 5/21 |
| W30 | 2 | W30-G2-S2 | CS-1420 part 5 | product | none | none | none | - | - | - | H019 1/13; H027 3/10; H030 1/9; H037 1/9; H056 1/7; H064 1/6; H101 1/4; H108 1/4 |
| W30 | 3 | W30-G3-S1 | CS-1257.11 | product | `tests/surface/` `test-standing_memo` | `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | none | - | v0.3.0 | extension filed by W28 | H041 2/9 |
| W30 | 3 | W30-G3-S2 | CS-1420 part 6 | product | none | none | none | - | - | - | H017 6/15; H030 2/9; H037 2/9; H056 2/7; H101 2/4 |
| W30 | filing | W30-F01 | U-079 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W30 | lane | W30-L01 | CS-849 | process | `tests/` `test-work_directory_left_absent` | `tools/provenance.tsv` | none | lane gap | - | - | H060 3/7 |
| W31 | 1 | W31-G1-S1 | CS-962.2 | product | `clockspeed/surface/web/` `panel_console`; `tests/surface/` `test-panel_console` | `tools/provenance.tsv` | none | - | v0.3.0 | child row filed by W29 | H001 24/45; H004 12/26; H007 12/25; H012 11/19; H016 9/15; H051 2/8; H073 4/6; H085 5/5 |
| W31 | 1 | W31-G1-S2 | CS-1426 part 1 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase5.md` | none | - | - | - | H013 6/17; H018 5/13; H019 2/13; H023 3/11; H024 3/11; H036 4/9; H041 3/9; H057 4/7; H063 4/6; H072 3/6 |
| W31 | 2 | W31-G2-S1 | CS-962.3 | product | none | `BACKLOG.md`, `tools/provenance.tsv` | none | - | v0.3.0 | child row filed by W29 | H001 25/45; H003 17/31; H007 13/25; H012 12/19; H016 10/15; H024 4/11; H051 3/8; H073 5/6; H097 4/4; H112 4/4 |
| W31 | 2 | W31-G2-S2 | CS-1420 part 7 | product | none | none | none | - | - | - | H027 4/10; H065 3/6 |
| W31 | 3 | W31-G3-S1 | U-079.1 unfiled | product | none | `docs/item_notes/phase6.md` | none | - | - | filed by W30 | H017 7/15; H019 3/13; H030 3/9; H078 2/5; H080 3/5; H091 2/4; H100 1/4; H101 3/4 |
| W31 | 3 | W31-G3-S2 | CS-843.1 | product | none | none | none | - | - | - | H011 4/20 |
| W31 | filing | W31-F01 | U-063 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W32 | 1 | W32-G1-S1 | CS-962.4 | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-960.md`, `tools/provenance.tsv` | none | - | v0.3.0 | child row filed by W29 | H008 7/23; H020 8/13; H051 4/8 |
| W32 | 1 | W32-G1-S2 | CS-1426 part 2 | product | none | none | none | - | - | - | H004 13/26; H006 6/26; H010 6/21 |
| W32 | 2 | W32-G2-S1 | U-063 unfiled | product | `shell/lib/` `login`; `shell/test/` `login.test` | none | `docs/OPERATIONS.md` | - | - | filed by W31 | H002 24/37; H005 18/26; H026 6/10; H035 5/9 |
| W32 | 2 | W32-G2-S2 | CS-1420 part 8 | product | none | none | none | - | - | - | H006 7/26; H010 7/21 |
| W32 | 3 | W32-G3-S1 | CS-1420 part 9 | product | none | none | none | - | - | - | H008 8/23; H041 4/9 |
| W32 | 3 | W32-G3-S2 | CS-1258.3 | product | none | none | none | - | - | extension filed by W13 | H006 8/26; H010 8/21; H111 2/4 |
| W33 | 1 | W33-G1-S1 | CS-1429 part 1 | product | none | `docs/LEDGER.md` | none | - | v0.3.0 | - | H013 7/17; H036 5/9; H057 5/7; H063 5/6 |
| W33 | 1 | W33-G1-S2 | CS-1420 part 10 | product | none | `ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/item_notes/phase5.md`, `tools/provenance.tsv` | none | - | - | - | - |
| W33 | 2 | W33-G2-S1 | CS-1398.2 | product | none | none | none | - | - | extension filed by W20 | H036 6/9; H057 6/7; H058 1/7; H078 3/5 |
| W33 | 2 | W33-G2-S2 | CS-1429 part 2 | product | none | none | none | - | v0.3.0 | - | H008 9/23; H009 11/21; H017 8/15; H018 6/13; H024 5/11; H072 4/6 |
| W33 | 3 | W33-G3-S1 | CS-1398.3 | product | none | none | none | - | - | extension filed by W20 | H030 4/9; H056 3/7; H078 4/5; H091 3/4 |
| W33 | 3 | W33-G3-S2 | CS-1429 part 3 | product | none | `docs/item_notes/phase5.md` | `BOOTSTRAP.md` | - | v0.3.0 | - | H001 26/45; H003 18/31; H006 9/26; H010 9/21 |
| W33 | filing | W33-F01 | U-075 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W33 | filing | W33-F02 | CS-1064 extension unfiled | product | none | `docs/item_notes/phase5.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W33 | filing | W33-F03 | CS-1254 extension unfiled | product | none | `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W33 | lane | W33-L01 | CS-474 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | lane gap | - | - | H022 1/12; H082 1/5 |
| W34 | 1 | W34-G1-S1 | CS-1254.1 | product | `clockspeed/progress/` `coverage`; `tests/progress/` `test-coverage` | `tools/provenance.tsv` | none | - | - | extension filed by W33 | - |
| W34 | 1 | W34-G1-S2 | CS-1398.4 | product | none | none | none | - | - | extension filed by W20 | H006 10/26; H008 10/23; H018 7/13; H023 4/11; H024 6/11 |
| W34 | 2 | W34-G2-S1 | U-075.1 unfiled | product | none | none | none | - | v0.3.0 | filed by W33 | H025 6/10; H028 6/10 |
| W34 | 2 | W34-G2-S2 | CS-1254.2 | product | none | none | none | - | - | extension filed by W33 | - |
| W34 | 3 | W34-G3-S1 | CS-1398.5 | product | `docs/adr/` `NNNN-cs-1398-SLUG` | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/adr/README.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md` | none | - | - | extension filed by W20 | H019 4/13 |
| W34 | 3 | W34-G3-S2 | CS-1064.1 | product | none | none | none | - | - | extension filed by W33 | H054 2/7; H059 2/7 |
| W34 | filing | W34-F01 | CS-1236 extension unfiled | product | none | `docs/item_notes/phase5.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W35 | 1 | W35-G1-S1 | CS-1254.3 | product | `tests/advisor/` `test-plan_adopt_built` | `tools/provenance.tsv` | none | - | - | extension filed by W33 | H019 5/13; H027 5/10; H030 5/9; H037 3/9; H056 4/7; H064 2/6; H108 2/4 |
| W35 | 1 | W35-G1-S2 | CS-1064.2 | product | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md` | none | - | - | extension filed by W33 | - |
| W35 | 2 | W35-G2-S1 | CS-1254.4 | product | none | none | none | - | - | extension filed by W33 | H013 8/17; H075 4/5 |
| W35 | 2 | W35-G2-S2 | CS-1422 part 1 | product | none | none | none | - | - | - | - |
| W35 | 3 | W35-G3-S1 | CS-1254.5 | product | none | none | none | - | - | extension filed by W33 | H027 6/10; H029 3/9; H065 4/6 |
| W35 | 3 | W35-G3-S2 | CS-1236.1 | product | `clockspeed/surface/api/` `overlay`; `tests/surface/` `test-overlay` | none | none | - | v0.4.0 | extension filed by W34 | H017 9/15 |
| W35 | filing | W35-F01 | U-003 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W36 | 1 | W36-G1-S1 | CS-1254.6 | product | `tests/advisor/` `test-plan_built` | `tools/provenance.tsv` | none | - | - | extension filed by W33 | H006 11/26; H010 10/21; H037 4/9 |
| W36 | 1 | W36-G1-S2 | CS-1258.4 | product | `tools/` `a11y_rules`; `tests/` `test-a11y_rules` | `tools/provenance.tsv` | none | - | - | extension filed by W13 | - |
| W36 | 2 | W36-G2-S1 | CS-1254.7 | product | none | `docs/ARCHITECTURE.md` | none | - | - | extension filed by W33 | H023 5/11; H041 5/9 |
| W36 | 2 | W36-G2-S2 | CS-1258.5 | product | none | none | none | - | - | extension filed by W13 | H088 4/5; H089 4/5 |
| W36 | 3 | W36-G3-S1 | U-075.2 unfiled | product | none | `docs/item_notes/phase4-followups-960.md` | none | - | v0.3.0 | filed by W33 | H025 7/10; H028 7/10 |
| W36 | 3 | W36-G3-S2 | U-003.1 unfiled | product | `docs/adr/` `NNNN-the-overlay-capability-boundary` | `docs/adr/README.md`, `tools/provenance.tsv` | none | - | v0.5.0 | filed by W35 | - |
| W36 | lane | W36-L01 | CS-613 | process | none | none | none | lane gap | - | - | H007 14/25 |
| W37 | 1 | W37-G1-S1 | CS-1421 | product | none | none | none | - | - | - | H006 12/26; H010 11/21; H023 6/11; H027 7/10; H030 6/9; H037 5/9; H041 6/9; H056 5/7; H064 3/6; H065 5/6; H108 3/4 |
| W37 | 1 | W37-G1-S2 | CS-1258.7 | product | none | none | none | - | - | extension filed by W13 | H001 27/45; H003 19/31; H004 14/26; H025 8/10; H028 8/10 |
| W37 | 2 | W37-G2-S1 | CS-1422 part 2 | product | none | none | none | - | - | - | H030 7/9; H056 6/7; H064 4/6; H108 4/4 |
| W37 | 2 | W37-G2-S2 | CS-1258.8 | product | `tests/surface/` `test-panel_a11y_rules` | `tools/provenance.tsv` | none | - | - | extension filed by W13 | - |
| W37 | 3 | W37-G3-S1 | CS-1051 | process | none | none | none | - | - | - | H008 11/23; H020 9/13 |
| W37 | 3 | W37-G3-S2 | CS-616 | process | none | `docs/item_notes/phase6.md` | none | - | - | - | H005 19/26 |
| W37 | filing | W37-F01 | U-054 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W37 | filing | W37-F02 | U-056 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W38 | 1 | W38-G1-S1 | CS-1422 part 3 | product | `tests/advisor/` `test-plan_power` | `BACKLOG.md`, `tools/provenance.tsv` | none | - | - | - | H023 7/11; H037 6/9; H041 7/9 |
| W38 | 1 | W38-G1-S2 | U-054 unfiled | product | `clockspeed/surface/web/` `panel_balance`; `tests/surface/` `test-panel_balance`; `clockspeed/audit/` `shortlist`; `tests/audit/` `test-shortlist` | `docs/item_notes/phase6.md` | none | - | v0.4.0 | filed by W37 | H001 28/45; H003 20/31; H004 15/26; H007 15/25; H008 12/23; H012 13/19; H016 11/15 |
| W38 | 2 | W38-G2-S1 | CS-1236.5 | product | `tests/advisor/` `test-overlay_trace` | none | none | - | v0.4.0 | extension filed by W34 | H013 9/17; H075 5/5; H080 4/5 |
| W38 | 2 | W38-G2-S2 | U-056.1 unfiled | product | none | none | none | - | - | filed by W37 | H001 29/45; H004 16/26; H025 9/10; H028 9/10 |
| W38 | 3 | W38-G3-S1 | CS-1236.2 | product | none | none | none | - | v0.4.0 | extension filed by W34 | - |
| W38 | 3 | W38-G3-S2 | CS-877 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-850.md` | none | - | - | - | H002 25/37; H005 20/26; H026 7/10; H035 6/9 |
| W38 | filing | W38-F01 | U-012 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W38 | filing | W38-F02 | U-064 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W39 | 1 | W39-G1-S1 | CS-1236.3 | product | none | none | `BOOTSTRAP.md` | - | v0.4.0 | extension filed by W34 | H001 30/45; H003 21/31; H007 16/25; H009 12/21; H033 6/9; H042 5/9; H045 6/8; H061 3/7; H062 5/7 |
| W39 | 1 | W39-G1-S2 | U-012.1 unfiled | product | `clockspeed/advisor/` `glance`; `tests/advisor/` `test-glance` | `tools/provenance.tsv` | none | - | v0.5.0 | filed by W38 | H013 10/17; H036 7/9 |
| W39 | 2 | W39-G2-S1 | CS-1236.6 | product | `tests/advisor/` `test-plan_preview` | none | none | - | v0.4.0 | extension filed by W34 | H013 11/17; H030 8/9; H041 8/9; H056 7/7; H064 5/6 |
| W39 | 2 | W39-G2-S2 | U-056.2 unfiled | product | none | none | none | - | - | filed by W37 | H001 31/45; H003 22/31; H004 17/26; H025 10/10; H028 10/10; H088 5/5; H089 5/5 |
| W39 | 3 | W39-G3-S1 | CS-1236.7 | product | none | none | none | - | v0.4.0 | extension filed by W34 | H027 8/10; H065 6/6 |
| W39 | 3 | W39-G3-S2 | U-064.1 unfiled | product | none | none | none | - | - | filed by W38 | H026 8/10; H035 7/9 |
| W39 | filing | W39-F01 | U-010 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W40 | 1 | W40-G1-S1 | CS-1236.8 | product | none | none | none | - | v0.4.0 | extension filed by W34 | H006 13/26; H008 13/23; H010 12/21; H018 8/13; H024 7/11; H027 9/10 |
| W40 | 1 | W40-G1-S2 | U-010 unfiled | product | none | `ROADMAP.md`, `docs/GATED.md`, `docs/LEDGER.md` | `docs/hud_doctrine.md` | - | v0.5.0 | filed by W39 | H053 6/8 |
| W40 | 2 | W40-G2-S1 | U-012.2 unfiled | product | `clockspeed/surface/api/` `glance`; `tests/surface/` `test-glance_route` | `docs/ARCHITECTURE.md`, `tools/provenance.tsv` | `BOOTSTRAP.md` | - | v0.5.0 | filed by W38 | H001 32/45; H003 23/31; H008 14/23; H009 13/21; H033 7/9; H042 6/9; H045 7/8; H061 4/7; H062 6/7 |
| W40 | 2 | W40-G2-S2 | CS-1243.1 | product | `clockspeed/audit/` `siting`; `tests/audit/` `test-siting` | `tools/provenance.tsv` | none | - | - | - | - |
| W40 | 3 | W40-G3-S1 | CS-1048.4 | product | none | none | none | - | - | extension filed by W2 | - |
| W40 | filing | W40-F01 | U-057 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W40 | lane | W40-L01 | CS-1001 | process | none | none | none | lane gap | - | - | - |
| W41 | 1 | W41-G1-S1 | U-012.3 unfiled | product | none | none | `docs/hud_doctrine.md` | - | v0.5.0 | filed by W38 | H001 33/45; H006 14/26; H008 15/23; H018 9/13; H023 8/11; H024 8/11; H041 9/9 |
| W41 | 1 | W41-G1-S2 | CS-1048.5 | product | none | none | none | - | - | extension filed by W2 | - |
| W41 | 2 | W41-G2-S1 | U-057.1 unfiled | product | none | none | none | - | - | filed by W40 | H047 8/8; H068 6/6 |
| W41 | 2 | W41-G2-S2 | CS-1249.1 | product | none | `config/lane_scopes.json` | none | - | - | - | - |
| W41 | 3 | W41-G3-S1 | U-057.2 unfiled | product | none | none | `docs/OPERATIONS.md` | - | - | filed by W40 | H002 26/37; H005 21/26 |
| W41 | 3 | W41-G3-S2 | CS-1048.3 | product | `clockspeed/audit/` `labels`; `tests/audit/` `test-labels` | none | none | - | - | extension filed by W2 | - |
| W41 | filing | W41-F01 | U-109 unfiled | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W42 | 1 | W42-G1-S1 | CS-1243.2 | product | `clockspeed/advisor/rules/` `siting`; `tests/advisor/rules/` `test-siting` | `tools/provenance.tsv` | none | - | - | - | - |
| W42 | 1 | W42-G1-S2 | CS-1048.6 | product | none | `BACKLOG.md`, `ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md`, `tools/provenance.tsv` | none | - | - | extension filed by W2 | - |
| W42 | 2 | W42-G2-S1 | CS-1243.3 | product | none | none | none | - | - | - | H013 12/17; H017 10/15; H019 6/13; H029 4/9; H058 2/7; H074 1/5 |
| W42 | 2 | W42-G2-S2 | U-109 unfiled | process | `clockspeed/audit/` `extraction`; `tests/audit/` `test-extraction` | `BACKLOG.md` | none | - | - | filed by W41 | H054 3/7; H059 3/7; H093 3/4; H110 3/4 |
| W42 | 3 | W42-G3-S1 | CS-1249.2 | product | `tests/solve/` `test-cycles` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md`, `tools/provenance.tsv` | none | - | - | - | H020 10/13 |
| W42 | 3 | W42-G3-S2 | CS-440.1 | product | none | none | none | - | - | - | - |
| W42 | filing | W42-F01 | CS-872 extension unfiled | product | none | `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W42 | filing | W42-F02 | CS-1047 child row A unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | after the CS-1047 doc slice (returned, unowned) | - |
| W42 | filing | W42-F03 | CS-1047 child row B unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | after the CS-1047 doc slice (returned, unowned) | - |
| W43 | 1 | W43-G1-S1 | CS-1047.8 | product | none | none | none | - | - | child row filed by W42 | H008 16/23; H093 4/4; H110 4/4 |
| W43 | 1 | W43-G1-S2 | CS-872.1 | product | none | none | `docs/OPERATIONS.md` | - | - | extension filed by W42 | H002 27/37; H005 22/26; H026 9/10; H035 8/9 |
| W43 | 2 | W43-G2-S1 | CS-1047.3 | product | none | none | none | - | - | child row filed by W42 | H001 34/45; H003 24/31; H115 3/4 |
| W43 | 2 | W43-G2-S2 | CS-1250 | product | `tests/audit/` `test-count_once` | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md`, `tools/provenance.tsv` | none | - | - | - | H020 11/13; H054 4/7; H059 4/7 |
| W43 | 3 | W43-G3-S1 | U-079.2 unfiled | product | none | `docs/item_notes/phase6.md` | none | - | - | filed by W30 | H017 11/15; H019 7/13; H030 9/9; H078 5/5; H080 5/5; H091 4/4; H100 2/4; H101 4/4 |
| W43 | 3 | W43-G3-S2 | CS-440.2 | product | none | none | none | - | - | - | H011 5/20; H081 1/5 |
| W43 | lane | W43-L01 | CS-1003 | process | none | none | none | lane gap | - | - | - |
| W44 | 1 | W44-G1-S1 | CS-1047.5 | product | none | none | none | - | - | child row filed by W42 | H071 5/6 |
| W44 | 1 | W44-G1-S2 | CS-1425 part 1 | product | `clockspeed/advisor/rules/` `production`; `tests/advisor/rules/` `test-production` | none | none | - | - | - | - |
| W44 | 2 | W44-G2-S1 | CS-1047.4 | product | none | none | none | - | - | child row filed by W42 | H004 18/26 |
| W44 | 2 | W44-G2-S2 | CS-1428 part 1 | product | none | none | `BOOTSTRAP.md` | - | - | - | H001 35/45; H003 25/31; H008 17/23; H009 14/21; H017 12/15; H018 10/13; H024 9/11; H033 8/9; H042 7/9; H045 8/8; H061 5/7; H062 7/7 |
| W44 | 3 | W44-G3-S1 | U-077.2 unfiled | process | none | none | none | - | - | filed by W4 | H001 36/45; H008 18/23 |
| W45 | 1 | W45-G1-S1 | CS-1047.6 | product | `clockspeed/surface/web/` `panel_plan`; `tests/surface/` `test-panel_plan` | `tools/provenance.tsv` | none | - | - | child row filed by W42 | - |
| W45 | 1 | W45-G1-S2 | CS-872.2 | product | `tests/surface/` `test-shortcuts` | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md`, `tools/provenance.tsv` | none | - | - | extension filed by W42 | H001 37/45; H003 26/31; H004 19/26; H006 15/26; H016 12/15; H071 6/6; H073 6/6; H084 4/5 |
| W45 | 2 | W45-G2-S1 | CS-1047.7 | product | `clockspeed/surface/web/` `panel_world_power`; `tests/surface/` `test-panel_world_power` | `tools/provenance.tsv` | none | - | - | child row filed by W42 | - |
| W45 | 2 | W45-G2-S2 | CS-1254.8 | product | none | `tools/provenance.tsv` | none | - | - | extension filed by W33 | H001 38/45; H003 27/31; H007 17/25; H012 14/19; H016 13/15; H051 5/8; H084 5/5 |
| W45 | 3 | W45-G3-S1 | CS-1047.1 | product | none | none | none | - | - | child row filed by W42 | H007 18/25; H012 15/19 |
| W45 | 3 | W45-G3-S2 | CS-1425 part 2 | product | none | none | none | - | - | - | H013 13/17; H058 3/7 |
| W45 | filing | W45-F01 | U-078 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W46 | 1 | W46-G1-S1 | CS-1047.2 | product | none | none | none | - | - | child row filed by W42 | H003 28/31; H016 14/15 |
| W46 | 1 | W46-G1-S2 | CS-1425 part 3 | product | none | none | none | - | - | - | H019 8/13; H023 9/11; H029 5/9; H058 4/7; H074 2/5; H079 3/5 |
| W46 | 2 | W46-G2-S1 | CS-1047.9 | product | none | none | none | - | - | child row filed by W42 | H001 39/45; H009 15/21; H051 6/8; H115 4/4 |
| W46 | 2 | W46-G2-S2 | U-078.1 unfiled | product | none | none | none | - | - | filed by W45 | H006 16/26; H010 13/21 |
| W46 | 3 | W46-G3-S1 | CS-1047.10 | product | none | `docs/item_notes/phase6.md`, `tools/provenance.tsv` | none | - | - | child row filed by W42 | H020 12/13 |
| W46 | 3 | W46-G3-S2 | CS-1425 part 4 | product | none | `ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md` | none | - | - | - | H058 5/7 |
| W46 | lane | W46-L01 | CS-1076 | process | none | none | none | lane gap | - | - | - |
| W47 | 1 | W47-G1-S1 | U-078.2 unfiled | product | none | none | none | - | - | filed by W45 | H066 2/6; H083 2/5 |
| W47 | 1 | W47-G1-S2 | CS-1058.1 | product | `tests/audit/` `test-network_edges`; `tests/audit/` `test-network_library` | none | none | - | - | extension filed by W3; child row filed by W3 | H054 5/7; H059 5/7 |
| W47 | 2 | W47-G2-S1 | CS-1428 part 2 | product | none | none | none | - | - | - | H001 40/45; H003 29/31; H006 17/26; H008 19/23; H009 16/21; H017 13/15; H018 11/13; H023 10/11; H024 10/11 |
| W47 | 2 | W47-G2-S2 | CS-1433 part 1 | product | `clockspeed/advisor/rules/` `materials`; `tests/advisor/rules/` `test-materials` | none | none | - | - | - | - |
| W47 | 3 | W47-G3-S1 | CS-1058.2 | product | none | none | none | - | - | extension filed by W3; child row filed by W3 | H054 6/7; H059 6/7 |
| W47 | 3 | W47-G3-S2 | U-125.2 unfiled | product | `tests/surface/` `test-oplog_redaction` | `tools/provenance.tsv` | none | - | - | filed by W20 | H007 19/25; H096 2/4 |
| W47 | filing | W47-F01 | U-022 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W48 | 1 | W48-G1-S1 | U-078.3 unfiled | product | none | `BACKLOG.md`, `docs/item_notes/phase6.md` | none | - | - | filed by W45 | H003 30/31; H004 20/26; H006 18/26; H010 14/21; H111 3/4 |
| W48 | 1 | W48-G1-S2 | U-022.1 unfiled | product | `clockspeed/solve/` `presets`; `tests/solve/` `test-presets` | `docs/ARCHITECTURE.md`, `tools/provenance.tsv` | none | - | - | filed by W47 | H107 2/4 |
| W48 | 2 | W48-G2-S1 | CS-1428 part 3 | product | none | none | none | - | - | - | H004 21/26; H006 19/26; H010 15/21 |
| W48 | 2 | W48-G2-S2 | CS-1427 part 1 | product | `clockspeed/solve/` `haul`; `tests/solve/` `test-haul` | `tools/provenance.tsv` | none | - | - | - | H107 3/4 |
| W48 | 3 | W48-G3-S1 | U-125.3 unfiled | product | `tests/surface/` `test-oplog_rotation` | `tools/provenance.tsv` | none | - | - | filed by W20 | H007 20/25; H096 3/4 |
| W48 | 3 | W48-G3-S2 | U-078.4 unfiled | product | none | none | none | - | - | filed by W45 | H004 22/26; H006 20/26; H010 16/21; H066 3/6; H083 3/5; H111 4/4 |
| W48 | filing | W48-F01 | U-047 unfiled | product | none | `ROADMAP.md`, `docs/item_notes/phase5.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W49 | 1 | W49-G1-S1 | CS-1431 part 1 | product | `clockspeed/advisor/rules/` `progress`; `tests/advisor/rules/` `test-progress` | `docs/LEDGER.md`, `tools/provenance.tsv` | none | - | - | - | H013 14/17; H014 6/16; H015 6/15; H019 9/13; H029 6/9; H058 6/7; H074 3/5; H079 4/5 |
| W49 | 1 | W49-G1-S2 | CS-1427 part 2 | product | `clockspeed/advisor/rules/` `transport`; `tests/advisor/rules/` `test-transport` | `tools/provenance.tsv` | none | - | - | - | - |
| W49 | 2 | W49-G2-S1 | CS-1433 part 2 | product | none | none | none | - | - | - | H013 15/17; H100 3/4 |
| W49 | 2 | W49-G2-S2 | U-047 unfiled | product | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase5.md` | none | - | - | filed by W48 | H014 7/16; H015 7/15; H019 10/13 |
| W49 | 3 | W49-G3-S1 | CS-458.1 | process | none | none | none | - | - | - | H011 6/20; H022 2/12 |
| W49 | filing | W49-F01 | U-066 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W50 | 1 | W50-G1-S1 | CS-1433 part 3 | product | none | none | none | - | - | - | H017 14/15; H019 11/13; H029 7/9; H037 7/9; H072 5/6; H074 4/5; H087 3/5; H100 4/4 |
| W50 | 1 | W50-G1-S2 | U-066 unfiled | product | none | `BACKLOG.md` | none | - | - | filed by W49 | H001 41/45; H004 23/26; H006 21/26; H010 17/21; H027 10/10 |
| W50 | 2 | W50-G2-S1 | CS-1058.5 | product | none | none | none | - | - | extension filed by W3; child row filed by W3 | H013 16/17; H019 12/13; H029 8/9; H036 8/9; H079 5/5 |
| W50 | 2 | W50-G2-S2 | U-125.9 unfiled | product | none | `tools/provenance.tsv` | none | - | - | filed by W20 | H007 21/25; H096 4/4 |
| W50 | 3 | W50-G3-S1 | CS-1433 part 4 | product | none | `ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md` | none | - | - | - | H037 8/9 |
| W50 | 3 | W50-G3-S2 | CS-807.1 | process | none | none | none | - | - | - | - |
| W50 | filing | W50-F01 | U-055 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W50 | filing | W50-F02 | U-067 unfiled | product | none | `ROADMAP.md`, `docs/item_notes/phase5.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W50 | lane | W50-L01 | CS-1071 | process | none | none | none | lane gap | - | - | - |
| W51 | 1 | W51-G1-S1 | U-055.1 unfiled | product | `tests/advisor/` `test-world_defaults` | `tools/provenance.tsv` | none | - | - | filed by W50 | H008 20/23; H033 9/9; H051 7/8; H064 6/6 |
| W51 | 1 | W51-G1-S2 | U-125.4 unfiled | product | none | none | none | - | - | filed by W20 | H021 10/12; H042 8/9; H087 4/5 |
| W51 | 2 | W51-G2-S1 | U-022.2 unfiled | product | none | none | none | - | - | filed by W47 | H006 22/26; H008 21/23; H086 5/5; H095 3/4 |
| W51 | 2 | W51-G2-S2 | CS-1431 part 2 | product | none | none | none | - | - | - | H009 17/21; H116 4/4 |
| W51 | 3 | W51-G3-S1 | U-125.5 unfiled | product | none | none | none | - | - | filed by W20 | H007 22/25; H012 16/19 |
| W51 | 3 | W51-G3-S2 | U-067 unfiled | product | none | none | none | - | - | filed by W50 | H001 42/45; H003 31/31; H004 24/26; H006 23/26; H008 22/23; H010 18/21; H016 15/15; H066 4/6; H083 4/5 |
| W51 | filing | W51-F01 | U-069 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W52 | 1 | W52-G1-S1 | CS-1427 part 3 | product | none | none | none | - | - | - | H013 17/17; H019 13/13; H029 9/9; H036 9/9; H058 7/7; H074 5/5 |
| W52 | 1 | W52-G1-S2 | CS-916.2 | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/GATED.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | - | H066 5/6; H095 4/4 |
| W52 | 2 | W52-G2-S1 | U-022.3 unfiled | product | none | none | none | - | - | filed by W47 | H006 24/26; H010 19/21; H061 6/7 |
| W52 | 2 | W52-G2-S2 | U-069 unfiled | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | none | - | - | filed by W51 | H001 43/45; H004 25/26 |
| W52 | filing | W52-F01 | U-070 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W53 | 1 | W53-G1-S1 | U-125.6 unfiled | product | none | none | none | - | - | filed by W20 | H009 18/21 |
| W53 | 1 | W53-G1-S2 | U-070 unfiled | product | none | none | none | - | - | filed by W52 | H001 44/45; H004 26/26; H066 6/6; H083 5/5 |
| W53 | 2 | W53-G2-S1 | U-125.7 unfiled | product | `shell/lib/` `oplog`; `shell/test/` `oplog.test`; `tests/shell/` `test-oplog_binding` | `tools/provenance.tsv` | none | - | - | filed by W20 | H002 28/37; H098 3/4; H099 3/4 |
| W53 | 2 | W53-G2-S2 | CS-1058.6 | product | none | none | none | - | - | extension filed by W3; child row filed by W3 | H054 7/7; H059 7/7 |
| W53 | 3 | W53-G3-S1 | U-055.2 unfiled | product | none | none | none | - | - | filed by W50 | H051 8/8 |
| W53 | 3 | W53-G3-S2 | CS-1431 part 3 | product | none | `docs/ARCHITECTURE.md` | none | - | - | - | H006 25/26; H008 23/23; H009 19/21; H010 20/21; H017 15/15; H018 12/13; H023 11/11; H024 11/11 |
| W53 | filing | W53-F01 | U-124 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W53 | lane | W53-L01 | CS-1074 | process | none | none | none | lane gap | - | - | - |
| W54 | 1 | W54-G1-S1 | U-125.10 unfiled | product | none | `tools/provenance.tsv` | none | - | - | filed by W20 | H002 29/37; H098 4/4; H099 4/4 |
| W54 | 1 | W54-G1-S2 | U-124.1 unfiled | product | `tests/advisor/` `test-store_recovery` | `tools/provenance.tsv` | none | - | - | filed by W53 | H057 7/7; H063 6/6 |
| W54 | 2 | W54-G2-S1 | U-125.8 unfiled | product | none | `BACKLOG.md`, `ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | `docs/OPERATIONS.md` | - | - | filed by W20 | H002 30/37; H005 23/26 |
| W54 | 2 | W54-G2-S2 | U-124.2 unfiled | product | none | none | none | - | - | filed by W53 | H009 20/21; H018 13/13; H021 11/12; H032 8/9; H042 9/9; H050 7/8; H072 6/6; H087 5/5 |
| W54 | 3 | W54-G3-S1 | U-124.3 unfiled | product | none | `docs/ARCHITECTURE.md` | none | - | - | filed by W53 | H006 26/26; H010 21/21 |
| W54 | filing | W54-F01 | U-092 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W54 | filing | W54-F02 | U-154 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W55 | 1 | W55-G1-S1 | CS-1262.1 | product | `clockspeed/surface/` `diagnostics`; `tests/surface/` `test-diagnostics` | `docs/item_notes/phase6.md`, `tools/provenance.tsv` | none | - | - | - | - |
| W55 | 1 | W55-G1-S2 | U-064.2 unfiled | product | none | none | `docs/OPERATIONS.md` | - | - | filed by W38 | H002 31/37; H005 24/26 |
| W55 | 2 | W55-G2-S1 | CS-1262.2 | product | `tests/surface/` `test-diagnostics_redaction` | `tools/provenance.tsv` | none | - | - | - | - |
| W55 | 2 | W55-G2-S2 | U-154.1 unfiled | product | `docs/adr/` `NNNN-the-oodle-data-licence-verdict` | `THIRD_PARTY.md`, `docs/LEDGER.md`, `docs/adr/README.md`, `tools/provenance.tsv` | none | - | - | filed by W54 | - |
| W55 | 3 | W55-G3-S1 | CS-1262.3 | product | `shell/lib/` `diagnostics`; `shell/test/` `diagnostics.test` | `tools/provenance.tsv` | none | - | - | - | H002 32/37 |
| W55 | 3 | W55-G3-S2 | U-092 unfiled | product | `tests/surface/` `test-response_headers` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md`, `tools/provenance.tsv` | none | - | - | filed by W54 | H007 23/25; H012 17/19 |
| W55 | filing | W55-F01 | U-090 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W55 | filing | W55-F02 | U-093 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W55 | filing | W55-F03 | U-121 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W56 | 1 | W56-G1-S1 | U-121.1 unfiled | product | none | `ROADMAP.md`, `docs/item_notes/phase6.md` | none | - | - | filed by W55 | H014 8/16; H015 8/15; H039 2/9 |
| W56 | 1 | W56-G1-S2 | U-154.2 unfiled | product | none | `docs/GATED.md`, `docs/LEDGER.md` | none | - | - | filed by W54 | - |
| W56 | 2 | W56-G2-S1 | CS-1262.4 | product | none | none | none | - | - | - | - |
| W56 | 2 | W56-G2-S2 | U-090 unfiled | product | `tests/surface/` `test-connection_discipline` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md`, `tools/provenance.tsv` | none | - | - | filed by W55 | H007 24/25; H012 18/19; H053 7/8 |
| W56 | 3 | W56-G3-S1 | CS-1262.5 | product | none | none | none | - | - | - | H002 33/37; H005 25/26 |
| W56 | 3 | W56-G3-S2 | U-093 unfiled | product | `tests/surface/` `test-internal_error` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | filed by W55 | H007 25/25; H012 19/19; H032 9/9; H050 8/8 |
| W56 | filing | W56-F01 | U-120 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W56 | filing | W56-F02 | U-122 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - | - |
| W56 | lane | W56-L01 | CS-460 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | lane gap | - | - | - |
| W57 | 1 | W57-G1-S1 | U-122 unfiled | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | none | - | - | filed by W56 | H001 45/45; H009 21/21 |
| W57 | 1 | W57-G1-S2 | U-120 unfiled | product | none | none | none | - | - | filed by W56 | H002 34/37; H005 26/26; H026 10/10; H035 9/9 |
| W57 | 2 | W57-G2-S1 | U-121.2 unfiled | product | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | none | - | - | filed by W55 | H053 8/8 |
| W57 | 2 | W57-G2-S2 | CS-1262.6 | product | none | `ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | `docs/OPERATIONS.md` | - | - | - | - |
| W57 | 3 | W57-G3-S1 | CS-452.1 | product | none | none | none | - | - | - | H031 3/9; H038 4/9; H040 6/9; H044 5/8 |
| W57 | 3 | W57-G3-S2 | CS-829.1 | product | none | none | none | - | - | - | H011 7/20 |
| W58 | 1 | W58-G1-S1 | CS-452.2 | product | none | none | none | - | - | - | H014 9/16; H022 3/12; H048 2/8; H049 3/8; H069 3/6; H081 2/5; H104 2/4; H105 3/4; H106 1/4 |
| W58 | 1 | W58-G1-S2 | CS-1150.1 | product | none | none | none | - | - | - | H011 8/20; H015 9/15 |
| W58 | 2 | W58-G2-S1 | CS-1241.1 | product | none | none | none | - | - | - | H092 4/4 |
| W58 | 2 | W58-G2-S2 | CS-452.3 | product | none | `ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | - | - | - | H037 9/9 |
| W58 | 3 | W58-G3-S1 | CS-984.1 | product | `tests/save/` `test-struct_interior_seam` | none | none | - | - | - | H011 9/20; H014 10/16; H015 10/15; H039 3/9 |
| W58 | 3 | W58-G3-S2 | CS-1089 | process | `tests/save/` `test-struct_interior_BLOCK` | `tools/provenance.tsv` | none | - | - | - | H048 3/8; H052 4/8; H070 1/6 |
| W59 | 1 | W59-G1-S1 | CS-832 | product | none | none | none | - | - | - | H011 10/20; H022 4/12 |
| W59 | 1 | W59-G1-S2 | CS-443.1 | product | none | none | none | - | - | - | H031 4/9; H038 5/9 |
| W59 | 2 | W59-G2-S1 | CS-829.2 | product | none | none | none | - | - | - | H011 11/20 |
| W59 | 2 | W59-G2-S2 | CS-1241.2 | product | `clockspeed/data/` `DECISIONS-TABLE`; `tests/data/` `test-build_variants`; `tests/data/` `test-decisions_table` | `config/lane_scopes.json` | none | - | - | - | - |
| W59 | 3 | W59-G3-S1 | CS-1150.2 | product | `tests/save/` `test-residual_redaction` | `tools/provenance.tsv` | none | - | - | - | H039 4/9 |
| W59 | 3 | W59-G3-S2 | CS-1091 | process | `tests/save/` `test-world_BLOCK` | `tools/provenance.tsv` | none | - | - | - | H014 11/16; H048 4/8; H052 5/8; H118 1/4 |
| W59 | lane | W59-L01 | CS-1241.3 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md`, `tools/provenance.tsv` | none | lane gap | - | - | H020 13/13 |
| W60 | 1 | W60-G1-S1 | CS-965.1 | product | none | none | none | - | - | - | H011 12/20; H081 3/5 |
| W60 | 1 | W60-G1-S2 | CS-984.2 | product | none | `docs/ARCHITECTURE.md`, `tools/provenance.tsv` | none | - | - | - | H022 5/12; H070 2/6 |
| W60 | 2 | W60-G2-S1 | CS-829.3 | product | none | none | none | - | - | - | H070 3/6 |
| W60 | 2 | W60-G2-S2 | CS-843.2 | product | none | none | none | - | - | - | H015 11/15 |
| W60 | 3 | W60-G3-S1 | CS-982 | product | `tests/save/` `test-tag_flag_evidence` | `tools/provenance.tsv` | none | - | - | - | H011 13/20; H039 5/9 |
| W60 | 3 | W60-G3-S2 | CS-443.2 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4.md` | none | - | - | - | H040 7/9; H044 6/8 |
| W60 | lane | W60-L01 | CS-446 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4.md` | none | lane gap | - | - | H069 4/6 |
| W61 | 1 | W61-G1-S1 | CS-965.2 | product | none | none | none | - | - | - | H014 12/16; H015 12/15; H022 6/12 |
| W61 | 1 | W61-G1-S2 | CS-462 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | - | - | - | H031 5/9; H038 6/9; H048 5/8 |
| W61 | 2 | W61-G2-S1 | CS-1053.1 | product | `tests/save/` `test-adr_0016_agreement` | none | none | - | - | - | H015 13/15; H117 1/4 |
| W61 | 2 | W61-G2-S2 | CS-986 | product | `tests/save/` `test-native_struct_population` | `tools/provenance.tsv` | none | - | - | - | H011 14/20; H039 6/9 |
| W61 | 3 | W61-G3-S1 | CS-828 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4-followups.md` | none | - | - | - | H011 15/20; H106 2/4 |
| W61 | 3 | W61-G3-S2 | CS-1053.2 | product | none | `docs/LEDGER.md`, `docs/adr/README.md`, `tools/provenance.tsv` | none | - | - | - | - |
| W62 | 1 | W62-G1-S1 | CS-861 | product | none | none | none | - | - | - | H031 6/9; H038 7/9 |
| W62 | 1 | W62-G1-S2 | CS-440.3 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4.md` | none | - | - | - | H014 13/16; H015 14/15 |
| W62 | 2 | W62-G2-S1 | CS-449.1 | product | none | none | none | - | - | - | H031 7/9; H038 8/9; H040 8/9; H044 7/8; H049 4/8 |
| W62 | 2 | W62-G2-S2 | CS-829.4 | product | none | none | none | - | - | - | - |
| W62 | 3 | W62-G3-S1 | CS-965.3 | product | `docs/adr/` `NNNN-cs-965-SLUG` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/adr/README.md`, `docs/item_notes/phase4-followups-960.md`, `tools/provenance.tsv` | none | - | - | - | - |
| W62 | 3 | W62-G3-S2 | CS-852.1 | process | none | none | none | - | - | - | H011 16/20; H031 8/9 |
| W63 | 1 | W63-G1-S1 | CS-843.3 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups.md` | none | - | - | - | H039 7/9; H070 4/6 |
| W63 | 1 | W63-G1-S2 | CS-1090 | process | `tests/save/` `test-properties_BLOCK` | `tools/provenance.tsv` | none | - | - | - | H022 7/12; H048 6/8; H052 6/8; H118 2/4 |
| W63 | 2 | W63-G2-S1 | CS-1052 | product | none | none | none | - | - | - | H014 14/16; H015 15/15; H039 8/9 |
| W63 | 2 | W63-G2-S2 | CS-988.1 | process | none | none | none | - | - | - | - |
| W63 | 3 | W63-G3-S1 | CS-988.2 | process | none | none | none | - | - | - | H069 5/6 |
| W63 | 3 | W63-G3-S2 | CS-860.1 | process | none | none | none | - | - | - | H060 4/7 |
| W63 | lane | W63-L01 | CS-1004 | process | none | none | none | lane gap | - | - | - |
| W64 | 1 | W64-G1-S1 | CS-1056.1 | process | `tests/save/` `test-oracle_pair_coverage` | none | none | - | - | - | - |
| W64 | 1 | W64-G1-S2 | CS-988.3 | process | none | none | none | - | - | - | - |
| W64 | 2 | W64-G2-S1 | CS-458.2 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | - | - | - | H070 5/6 |
| W64 | 2 | W64-G2-S2 | CS-988.4 | process | none | none | none | - | - | - | H048 7/8; H107 4/4 |
| W64 | 3 | W64-G3-S1 | CS-412.1 | process | none | none | none | - | - | - | H011 17/20; H039 9/9; H081 4/5 |
| W64 | 3 | W64-G3-S2 | CS-1358.1 | process | `tests/` `tree_population`; `tests/` `test-tree_population` | none | none | - | - | - | H060 5/7; H117 2/4 |
| W65 | 1 | W65-G1-S1 | CS-455 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | - | - | - | H011 18/20; H022 8/12; H049 5/8; H082 2/5 |
| W65 | 1 | W65-G1-S2 | CS-1358.2 | process | none | none | none | - | - | - | H002 35/37; H102 1/4; H109 1/4 |
| W65 | 2 | W65-G2-S1 | CS-943 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4-followups-900.md` | none | - | - | - | - |
| W65 | 2 | W65-G2-S2 | CS-1092 | process | none | none | none | - | - | - | H052 7/8; H117 3/4 |
| W65 | 3 | W65-G3-S1 | CS-860.2 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | - | - | - | H082 3/5 |
| W65 | 3 | W65-G3-S2 | CS-1131 | process | `tests/data/` `test-drift_guard_work_items_orphans` | `tools/provenance.tsv` | none | - | - | - | H090 2/5; H102 2/4 |
| W66 | 1 | W66-G1-S1 | CS-1010.1 | process | none | none | none | - | - | - | - |
| W66 | 1 | W66-G1-S2 | CS-1077 | process | none | none | none | - | - | - | H109 2/4 |
| W66 | 2 | W66-G2-S1 | CS-988.5 | process | none | none | none | - | - | - | H014 15/16; H022 9/12 |
| W66 | 2 | W66-G2-S2 | CS-852.2 | process | none | none | none | - | - | - | - |
| W66 | 3 | W66-G3-S1 | CS-945.1 | process | `tools/` `branch_census`; `tests/` `test-branch_census` | none | none | - | - | - | - |
| W66 | 3 | W66-G3-S2 | CS-1010.2 | process | none | none | none | - | - | - | - |
| W66 | lane | W66-L01 | CS-1010.3 | process | none | `docs/item_notes/phase4-followups-1000.md` | none | lane gap | - | - | - |
| W67 | 1 | W67-G1-S1 | CS-855.1 | process | none | none | none | - | - | - | - |
| W67 | 1 | W67-G1-S2 | CS-988.6 | process | none | none | none | - | - | - | - |
| W67 | 2 | W67-G2-S1 | CS-910.1 | process | none | `config/lane_scopes.json` | none | - | - | - | - |
| W67 | 2 | W67-G2-S2 | CS-1149.1 | process | none | none | none | - | - | - | H011 19/20 |
| W67 | 3 | W67-G3-S1 | CS-859 | process | none | none | none | - | - | - | - |
| W67 | 3 | W67-G3-S2 | CS-1358.3 | process | none | none | none | - | - | - | H052 8/8; H061 7/7; H118 3/4; H121 4/4 |
| W68 | 1 | W68-G1-S1 | CS-1094 | process | none | none | none | - | - | - | H117 4/4 |
| W68 | 1 | W68-G1-S2 | CS-1078 | process | none | none | none | - | - | - | - |
| W68 | 2 | W68-G2-S1 | CS-499.1 | process | none | none | none | - | - | - | H022 10/12; H049 6/8; H069 6/6; H081 5/5; H104 3/4 |
| W68 | 2 | W68-G2-S2 | CS-1055.1 | process | `tests/` `write_tracer` | none | none | - | - | - | H060 6/7 |
| W68 | 3 | W68-G3-S1 | CS-910.2 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | - | H119 4/4; H120 4/4 |
| W68 | 3 | W68-G3-S2 | CS-1063 | process | none | `docs/item_notes/phase4-followups-1000.md` | none | - | - | - | H090 3/5; H102 3/4 |
| W69 | 1 | W69-G1-S1 | CS-1130.2 | process | `tools/` `ACCEPTANCE-CLAUSE-PIN-RECORD` | `docs/LEDGER.md`, `tools/provenance.tsv` | none | - | - | - | - |
| W69 | 1 | W69-G1-S2 | CS-1149.2 | process | `tests/save/` `test-residual_census` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4-followups-1000.md`, `docs/item_notes/phase4-followups.md`, `tools/provenance.tsv` | none | - | - | - | H106 3/4 |
| W69 | 2 | W69-G2-S1 | CS-1075.1 | process | none | none | none | - | - | - | H109 3/4 |
| W69 | 2 | W69-G2-S2 | CS-1295.1 | process | `docs/_archive/` `DATE-cs1295-repo-review-plan-2`; `docs/_archive/` `DATE-cs1295-repo-review-findings-2` | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase7.md`, `tools/provenance.tsv` | none | - | - | - | - |
| W69 | 3 | W69-G3-S1 | CS-439.1 | process | none | none | none | - | - | - | H040 9/9; H044 8/8 |
| W69 | 3 | W69-G3-S2 | CS-946 | process | `docs/adr/` `NNNN-cs-946-SLUG` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/adr/README.md`, `docs/item_notes/phase4-followups-900.md`, `tools/provenance.tsv` | none | - | - | - | - |
| W70 | 1 | W70-G1-S1 | CS-1129 | process | none | none | none | - | - | - | H090 4/5 |
| W70 | 1 | W70-G1-S2 | CS-807.2 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups.md` | none | - | - | - | H049 7/8; H104 4/4 |
| W70 | 2 | W70-G2-S1 | CS-499.2 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | - | - | - | H014 16/16; H105 4/4; H106 4/4 |
| W70 | 2 | W70-G2-S2 | CS-966 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4-followups-960.md` | none | - | - | - | - |
| W70 | 3 | W70-G3-S1 | CS-1055.2 | process | `tests/` `test-live_copies_guard`; `tests/` `test-write_tracer` | `tools/provenance.tsv` | `docs/OPERATIONS.md` | - | - | - | - |
| W70 | 3 | W70-G3-S2 | CS-439.2 | process | `tests/` `test-silent_loss_guard` | none | none | - | - | - | H031 9/9; H038 9/9 |
| W70 | lane | W70-L01 | CS-1141 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-1000.md` | none | lane gap | - | - | - |
| W71 | 1 | W71-G1-S1 | CS-988.7 | process | none | none | none | - | - | - | - |
| W71 | 1 | W71-G1-S2 | CS-1056.2 | process | none | `tools/provenance.tsv` | none | - | - | - | H049 8/8; H070 6/6; H082 4/5 |
| W71 | 2 | W71-G2-S1 | CS-1137 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-1000.md` | none | - | - | - | - |
| W71 | 2 | W71-G2-S2 | CS-945.2 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `tools/provenance.tsv` | none | - | - | - | - |
| W71 | 3 | W71-G3-S1 | CS-472.1 | process | none | none | none | - | - | - | H011 20/20; H022 11/12 |
| W71 | 3 | W71-G3-S2 | CS-1075.2 | process | none | none | none | - | - | - | H109 4/4 |
| W72 | 1 | W72-G1-S1 | CS-604 | process | none | `BACKLOG.md` | `BOOTSTRAP.md`, `docs/OPERATIONS.md` | - | - | - | H002 36/37; H090 5/5; H102 4/4 |
| W72 | 1 | W72-G1-S2 | CS-1358.4 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase7.md`, `tools/provenance.tsv` | none | - | - | - | - |
| W72 | 2 | W72-G2-S1 | CS-610 | process | none | none | none | - | - | - | H060 7/7 |
| W72 | 2 | W72-G2-S2 | CS-1295.2 | process | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase7.md`, `tools/provenance.tsv` | none | - | - | - | - |
| W72 | 3 | W72-G3-S1 | CS-477.1 | process | none | none | none | - | - | - | H022 12/12; H082 5/5 |
| W72 | 3 | W72-G3-S2 | CS-615 | process | `shell/` `suite_counts` | `tools/provenance.tsv` | none | - | - | - | H002 37/37 |
| W73 | 1 | W73-G1-S1 | CS-606 | process | `tests/surface/` `test-entry_serve` | `docs/item_notes/phase6.md`, `tools/provenance.tsv` | none | - | - | - | H021 12/12 |
| W73 | 1 | W73-G1-S2 | CS-855.2 | process | none | none | none | - | - | - | H118 4/4 |
| W73 | lane | W73-L01 | CS-1135 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-1000.md` | none | lane gap | - | - | H048 8/8 |

### Hub files

| hub | file | kind | writers |
|---|---|---|---|
| H001 | `tests/surface/test_web_assets.py` | file | 45 |
| H002 | `tests/shell/test_shell_assets.py` | file | 37 |
| H003 | `clockspeed/surface/web/app.js` | file | 31 |
| H004 | `clockspeed/surface/web/app.css` | file | 26 |
| H005 | `shell/main.js` | file | 26 |
| H006 | `tests/surface/test_panel_advice.py` | file | 26 |
| H007 | `tests/surface/test_server.py` | file | 25 |
| H008 | `tests/surface/audit_harness.py` | file | 23 |
| H009 | `clockspeed/surface/providers.py` | file | 21 |
| H010 | `clockspeed/surface/web/panel_advice.js` | file | 21 |
| H011 | `clockspeed/save/objects.py` | file | 20 |
| H012 | `clockspeed/surface/server.py` | file | 19 |
| H013 | `clockspeed/advisor/advise.py` | file | 17 |
| H014 | `tests/save/test_world.py` | file | 16 |
| H015 | `clockspeed/save/world.py` | file | 15 |
| H016 | `clockspeed/surface/web/index.html` | file | 15 |
| H017 | `tests/surface/test_advice_source.py` | file | 15 |
| H018 | `clockspeed/surface/api/advice.py` | file | 13 |
| H019 | `tests/advisor/test_every_rule_fires.py` | file | 13 |
| H020 | `tests/ops/test_lane_scope.py` | file | 13 |
| H021 | `clockspeed/surface/__main__.py` | file | 12 |
| H022 | `tests/save/test_properties.py` | file | 12 |
| H023 | `tests/surface/golden/advice_no_target.json` | file | 11 |
| H024 | `tests/surface/test_advice.py` | file | 11 |
| H025 | `clockspeed/surface/web/` `panel_play` | file | 10 |
| H026 | `shell/test/window.test.js` | file | 10 |
| H027 | `tests/surface/test_flow_view.py` | file | 10 |
| H028 | `tests/surface/` `test-panel_play` | file | 10 |
| H029 | `clockspeed/advisor/ranking.py` | file | 9 |
| H030 | `clockspeed/advisor/rules/plan.py` | file | 9 |
| H031 | `clockspeed/data/locate.py` | file | 9 |
| H032 | `clockspeed/surface/api/contract.py` | file | 9 |
| H033 | `clockspeed/surface/api/routes.py` | file | 9 |
| H034 | `installer/cli` | file | 9 |
| H035 | `shell/lib/window.js` | file | 9 |
| H036 | `tests/advisor/test_advise.py` | file | 9 |
| H037 | `tests/advisor/test_plan_world.py` | file | 9 |
| H038 | `tests/data/test_locate.py` | file | 9 |
| H039 | `tests/save/synthetic.py` | file | 9 |
| H040 | `tests/save/test_workdir.py` | file | 9 |
| H041 | `tests/surface/test_advice_golden.py` | file | 9 |
| H042 | `tests/surface/test_routes.py` | file | 9 |
| H043 | `README.md` | file | 8 |
| H044 | `clockspeed/save/workdir.py` | file | 8 |
| H045 | `clockspeed/surface/api/health.py` | file | 8 |
| H046 | `shell/test/supervisor.test.js` | file | 8 |
| H047 | `shell/test/tray.test.js` | file | 8 |
| H048 | `tests/data/test_phase2_gate.py` | file | 8 |
| H049 | `tests/save/reach_guard.py` | file | 8 |
| H050 | `tests/surface/test_contract.py` | file | 8 |
| H051 | `tests/surface/test_panel_scope.py` | file | 8 |
| H052 | `tests/test_citation_tables.py` | file | 8 |
| H053 | `tools/measurements.json` | file | 8 |
| H054 | `clockspeed/audit/__init__.py` | file | 7 |
| H055 | `shell/lib/supervisor.js` | file | 7 |
| H056 | `tests/advisor/rules/test_plan.py` | file | 7 |
| H057 | `tests/advisor/test_ledger.py` | file | 7 |
| H058 | `tests/advisor/test_world_advice.py` | file | 7 |
| H059 | `tests/audit/test_package_exports.py` | file | 7 |
| H060 | `tests/conftest.py` | file | 7 |
| H061 | `tests/surface/test_acceptance.py` | file | 7 |
| H062 | `tests/surface/test_health.py` | file | 7 |
| H063 | `clockspeed/advisor/ledger.py` | file | 6 |
| H064 | `clockspeed/advisor/plans.py` | file | 6 |
| H065 | `clockspeed/surface/api/flow_view.py` | file | 6 |
| H066 | `clockspeed/surface/web/panel_registry.js` | file | 6 |
| H067 | `installer/engine` | file | 6 |
| H068 | `shell/lib/tray.js` | file | 6 |
| H069 | `tests/save/test_phase4_gate.py` | file | 6 |
| H070 | `tests/save/test_struct_interior.py` | file | 6 |
| H071 | `tests/surface/panel_harness.py` | file | 6 |
| H072 | `tests/surface/test_advice_act.py` | file | 6 |
| H073 | `tests/surface/test_panel_global_scope.py` | file | 6 |
| H074 | `clockspeed/advisor/rules/__init__.py` | file | 5 |
| H075 | `clockspeed/advisor/trace.py` | file | 5 |
| H076 | `config/` `runtime_pins` | file | 5 |
| H077 | `installer/manifest` | file | 5 |
| H078 | `tests/advisor/test_cards.py` | file | 5 |
| H079 | `tests/advisor/test_ranking.py` | file | 5 |
| H080 | `tests/advisor/test_trace.py` | file | 5 |
| H081 | `tests/save/test_objects.py` | file | 5 |
| H082 | `tests/save/test_value_anchoring.py` | file | 5 |
| H083 | `tests/surface/test_panel_registry.py` | file | 5 |
| H084 | `tests/surface/test_panel_seam.py` | file | 5 |
| H085 | `tests/surface/test_panel_solve.py` | file | 5 |
| H086 | `tests/surface/test_registry.py` | file | 5 |
| H087 | `tests/surface/test_schematic_source.py` | file | 5 |
| H088 | `tests/test_dashboard_probe.py` | file | 5 |
| H089 | `tools/dashboard_probe.py` | file | 5 |
| H090 | `tools/drift_guard.py` | file | 5 |
| H091 | `clockspeed/advisor/cards.py` | file | 4 |
| H092 | `clockspeed/data/registry.py` | file | 4 |
| H093 | `clockspeed/surface/api/map.py` | file | 4 |
| H094 | `clockspeed/surface/api/power.py` | file | 4 |
| H095 | `clockspeed/surface/api/registry.py` | file | 4 |
| H096 | `clockspeed/surface/` `oplog` | file | 4 |
| H097 | `clockspeed/surface/web/panel_power.js` | file | 4 |
| H098 | `shell/lib/endpoint.js` | file | 4 |
| H099 | `shell/test/endpoint.test.js` | file | 4 |
| H100 | `tests/advisor/test_display_name_keying.py` | file | 4 |
| H101 | `tests/advisor/test_plan_redesign.py` | file | 4 |
| H102 | `tests/data/test_drift_guard_data.py` | file | 4 |
| H103 | `tests/` `installer/test-manifest` | file | 4 |
| H104 | `tests/save/test_reach_guard.py` | file | 4 |
| H105 | `tests/save/test_synthetic.py` | file | 4 |
| H106 | `tests/save/test_trailing_run.py` | file | 4 |
| H107 | `tests/solve/test_phase3_gate.py` | file | 4 |
| H108 | `tests/solve/test_plan_edges.py` | file | 4 |
| H109 | `tests/sphinx_role_guard.py` | file | 4 |
| H110 | `tests/surface/test_map.py` | file | 4 |
| H111 | `tests/surface/test_panel_advice_layout.py` | file | 4 |
| H112 | `tests/surface/test_panel_power.py` | file | 4 |
| H113 | `tests/surface/test_power.py` | file | 4 |
| H114 | `tests/surface/test_solve.py` | file | 4 |
| H115 | `tests/surface/` `test-views` | file | 4 |
| H116 | `tests/surface/test_world_provider_memo.py` | file | 4 |
| H117 | `tests/test_docs_citations.py` | file | 4 |
| H118 | `tests/test_exception_rendering.py` | file | 4 |
| H119 | `tests/test_make_cert.py` | file | 4 |
| H120 | `tests/test_make_shortcut.py` | file | 4 |
| H121 | `tests/test_readme_audit.py` | file | 4 |
| H122 | `tests/` `test-runtime_pins` | file | 4 |
| D1 | `docs/OPERATIONS.md` | document | 0 |
| D2 | `docs/hud_doctrine.md` | document | 0 |
| D3 | `BOOTSTRAP.md` | document | 0 |
