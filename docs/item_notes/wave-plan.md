# Clockspeed - the wave plan, an annex

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**This file is an ANNEX to `docs/item_notes.md`, not a phase leaf.** It carries no item
section and no `## CS-nnn` heading, so `tools/drift_guard.py` guard (j) neither routes to
it nor reads a section out of it. It holds the wave table of the session 159 plan, one
row per slice, and pointers; every rule it depends on is owned elsewhere and named here.

**Pointers - each fact has one owner:**

- Each row's item line: `ROADMAP.md`.
- Each row's acceptance, write-list, wave id and hub-chain place: its section in its leaf,
  found through the leaf table in `docs/item_notes.md`.
- The map from plan key to CS id, and each filing batch's record: `docs/LEDGER.md`.
- Conditional rows and their triggers: `BACKLOG.md`.
- Lane scopes: `config/lane_scopes.json`.
- Provenance rows for new tracked files: `tools/provenance.tsv`.
- The hand-off a cold session starts from: `CS-NEXT-SESSION.txt`.
- Each row's Write-list cell: `docs/item_notes/wave-plan-write-lists.md`, by its Slice cell.

Re-pack tools: <sidecars>/CS/plan-s159-tools/ - the five plan files of planning session 159, sha256 values in their docs/LEDGER.md copy record.

## Wave table

| Wave | Group | Slice | Item | Class | New files | Landing files | Hub text owed | Lane scope | Milestone | Entry conditions |
|---|---|---|---|---|---|---|---|---|---|---|
| W0a | merger | W0a-M01 | U-158 not filed | process | none | `docs/item_notes/wave-plan.md` | none | - | - | - |
| W0a | merger | W0a-M02 | CS-1406 part 1 | process | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-850.md`, `docs/item_notes/phase4.md`, `docs/item_notes/phase7.md` | none | - | - | - |
| W0a | merger | W0a-M03 | CS-1406 part 2 | process | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups.md`, `docs/item_notes/phase4.md` | none | - | - | - |
| W0a | merger | W0a-M04 | CS-1406 part 3 | process | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-850.md`, `docs/item_notes/phase4-followups-900.md`, `docs/item_notes/phase4-followups.md` | none | - | - | - |
| W0a | merger | W0a-M05 | CS-1406 part 4 | process | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-1000.md`, `docs/item_notes/phase4-followups-960.md`, `docs/item_notes/phase6.md` | none | - | - | - |
| W0a | merger | W0a-M06 | CS-1406 part 5 | process | none | `BACKLOG.md`, `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md`, `docs/item_notes/phase7.md` | none | - | - | - |
| W0a | merger | W0a-M07 | CS-1406 part 6 | process | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase7.md` | none | - | - | - |
| W0a | merger | W0a-M08 | U-145 not filed | process | none | `CS-NEXT-SESSION.txt`, `docs/GATED.md`, `docs/LEDGER.md` | none | - | - | - |
| W0b | merger | W0b-M01 | CS-1419 part 1 | process | none | `WAKEUP_NOTES.md` | none | - | - | - |
| W0b | merger | W0b-M02 | CS-1419 part 2 | process | none | `CS-NEXT-SESSION.txt`, `docs/LEDGER.md` | none | - | - | - |
| W0b | merger | W0b-M03 | CS-1409 part 1 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase7.md`, `docs/item_notes/wave-plan.md`, `tools/provenance.tsv` | none | - | - | - |
| W0b | merger | W0b-M04 | CS-1409 part 2 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase5.md` | none | - | - | - |
| W0b | merger | W0b-M05 | CS-1409 part 3 | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | none | - | - | - |
| W0b | merger | W0b-M06 | CS-1409 part 4 | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | none | - | - | - |
| W0b | merger | W0b-M07 | CS-1409 part 5 | process | none | `BACKLOG.md`, `docs/LEDGER.md`, `docs/item_notes/phase4-followups-960.md`, `docs/item_notes/phase5.md`, `docs/item_notes/phase6.md`, `docs/item_notes/phase7.md` | none | - | - | - |
| W0b | merger | W0b-M08 | CS-1409 part 6 | process | none | `CS-NEXT-SESSION.txt`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase7.md`, `docs/item_notes/wave-plan.md` | none | - | - | - |
| W0b | merger | W0b-M09 | CS-1412 | process | none | `docs/item_notes/wave-plan.md` | none | - | - | - |
| W0b | merger | W0b-M10 | CS-1413 | process | none | `CS-NEXT-SESSION.txt`, `docs/LEDGER.md` | none | - | - | - |
| W0b | merger | W0b-M11 | CS-1411 | process | none | `docs/LEDGER.md`, `docs/item_notes/wave-plan.md` | `docs/OPERATIONS.md` | - | - | - |
| W0b | merger | W0b-M12 | CS-1414 | process | none | `docs/item_notes/wave-plan.md` | `docs/OPERATIONS.md` | - | - | - |
| W0b | merger | W0b-M13 | CS-1415 | process | none | `docs/item_notes/wave-plan.md` | none | - | - | - |
| W0b | merger | W0b-M14 | CS-1417 | process | none | `CS-NEXT-SESSION.txt`, `config/lane_scopes.json`, `docs/item_notes/wave-plan.md` | `docs/OPERATIONS.md` | - | - | - |
| W0b | merger | W0b-M15 | CS-1418 | process | none | `docs/LEDGER.md` | none | - | - | - |
| W0b | merger | W0b-M16 | CS-1366 | process | none | `BACKLOG.md`, `CS-NEXT-SESSION.txt`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase7.md` | none | - | - | - |
| W0a | 1 | W0-G1-S1 | CS-913.1 | product | none | none | none | - | - | - |
| W0a | 1 | W0-G1-S2 | CS-425; CS-448; CS-489; CS-492; CS-614; CS-701; CS-839; CS-840; CS-841; CS-842; CS-938; CS-941; CS-976; CS-981; CS-993; CS-1007; CS-1119; CS-1255; CS-1259; U-001 not filed; U-113 not filed; U-139 not filed; U-155 not filed | process; product | none | `BACKLOG.md`, `CS-NEXT-SESSION.txt`, `ROADMAP.md`, `config/lane_scopes.json`, `docs/GATED.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-1000.md`, `docs/item_notes/phase4-followups-900.md`, `docs/item_notes/phase4-followups-960.md`, `docs/item_notes/phase4-followups.md`, `docs/item_notes/phase4.md`, `docs/item_notes/phase6.md`, `docs/item_notes/phase7.md` | none | - | - | - |
| W0a | 2 | W0-G2-S1 | CS-914 | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | - |
| W0a | 2 | W0-G2-S2 | CS-1248.1 | product | `clockspeed/solve/quantity.py`, `tests/solve/test_quantity.py` | none | none | - | - | - |
| W1 | 1 | W1-G1-S1 | CS-1439 part 1 | process | `clockspeed/surface/web/` `panel_diagnostics`, `tests/surface/` `test-panel_diagnostics` | none | none | - | - | wave per its leaf |
| W1 | 1 | W1-G1-S2 | CS-1401 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md` | none | - | v0.3.0 | - |
| W1 | 2 | W1-G2-S1 | CS-1439 part 2 | process | none | none | none | - | - | wave per its leaf |
| W1 | 2 | W1-G2-S2 | CS-454.1 | product | none | none | none | - | - | - |
| W1 | 3 | W1-G3-S1 | CS-1261 | product | `docs/adr/` `NNNN-cs-1261-SLUG` | none | none | - | - | - |
| W1 | 3 | W1-G3-S2 | CS-1410 | process | none | none | none | - | - | - |
| W1 | lane | W1-L01 | CS-887 | product | `tests/surface/` `test-exit_codes` | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md`, `tools/provenance.tsv` | `docs/OPERATIONS.md` | lane gap | - | - |
| W2 | 1 | W2-G1-S1 | CS-1439 part 3 | process | none | none | none | - | - | - |
| W2 | 1 | W2-G1-S2 | CS-936.1 | process | `tests/` `test-scrub_era_refs`, `tools/` `scrub_era_refs` | none | none | - | - | - |
| W2 | 2 | W2-G2-S1 | CS-1204 | product | none | none | none | - | v0.2.0 | - |
| W2 | 2 | W2-G2-S2 | CS-454.2 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | - | - | - |
| W2 | 3 | W2-G3-S1 | CS-909 | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | - |
| W2 | 3 | W2-G3-S2 | CS-1243.4 | product | `docs/adr/` `NNNN-the-degraded-d1-siting-form` | `BACKLOG.md`, `docs/adr/README.md`, `docs/item_notes/phase5.md`, `tools/provenance.tsv` | `BOOTSTRAP.md` | - | - | - |
| W2 | filing | W2-F01 | CS-1048 extension unfiled | product | none | `docs/item_notes/phase5.md`, `docs/LEDGER.md` | none | - | - | - |
| W3 | 1 | W3-G1-S1 | CS-619.1 | process | `shell/lib/` `persist`, `shell/test/` `persist.test` | `tools/provenance.tsv` | none | - | - | - |
| W3 | 1 | W3-G1-S2 | CS-1438 | product | none | `ROADMAP.md`, `THIRD_PARTY.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | `docs/OPERATIONS.md` | - | v0.2.0 | - |
| W3 | 2 | W3-G2-S1 | CS-1437 part 1 | product | `tests/surface/` `test-admission` | none | none | - | - | - |
| W3 | 2 | W3-G2-S2 | CS-1440 part 1 | product | `tests/data/` `test-data_root` | none | none | - | v0.2.0 | - |
| W3 | 3 | W3-G3-S1 | CS-1436 part 1 | product | `tests/surface/` `test-web_palette` | `config/lane_scopes.json`, `tools/provenance.tsv` | none | - | - | - |
| W3 | 3 | W3-G3-S2 | CS-1048.1 | product | `clockspeed/advisor/` `annotations`, `tests/advisor/` `test-annotations` | none | none | - | - | extension filed by W2 |
| W3 | filing | W3-F01 | CS-1058 extension unfiled | product | none | `docs/item_notes/phase5.md`, `docs/LEDGER.md` | none | - | - | - |
| W3 | filing | W3-F02 | CS-1058 child row unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase5.md`, `docs/LEDGER.md` | none | - | - | - |
| W3 | lane | W3-L01 | CS-618 | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | lane gap | - | - |
| W4 | 1 | W4-G1-S1 | CS-1437 part 2 | product | none | none | none | - | - | - |
| W4 | 1 | W4-G1-S2 | CS-1434 part 1 | product | `tests/surface/` `test-views` | none | none | - | v0.3.0 | - |
| W4 | 2 | W4-G2-S1 | CS-1437 part 3 | product | none | `docs/item_notes/phase6.md` | none | - | - | - |
| W4 | 2 | W4-G2-S2 | CS-1440 part 2 | product | none | none | none | - | v0.2.0 | - |
| W4 | 3 | W4-G3-S1 | CS-1048.2 | product | none | none | none | - | - | extension filed by W2 |
| W4 | 3 | W4-G3-S2 | CS-1058.3 | product | none | none | none | - | - | extension filed by W3; child row filed by W3 |
| W4 | filing | W4-F01 | U-077 unfiled | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W5 | 1 | W5-G1-S1 | CS-1434 part 2 | product | none | none | none | - | v0.3.0 | - |
| W5 | 1 | W5-G1-S2 | CS-1440 part 3 | product | none | `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `tools/provenance.tsv` | `docs/OPERATIONS.md` | - | v0.2.0 | - |
| W5 | 2 | W5-G2-S1 | CS-1435 part 1 | product | `scripts/` `make_icon`, `tests/` `test-make_icon`, `shell/lib/` `identity`, `shell/test/` `identity.test` | none | none | - | v0.2.0 | - |
| W5 | 2 | W5-G2-S2 | U-077.1 unfiled | process | none | `BACKLOG.md` | `docs/OPERATIONS.md` | - | - | filed by W4 |
| W5 | 3 | W5-G3-S1 | CS-1058.4 | product | none | none | none | - | - | extension filed by W3; child row filed by W3 |
| W5 | 3 | W5-G3-S2 | CS-1427 part 5 | product | none | none | none | - | - | - |
| W5 | filing | W5-F01 | U-060 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W5 | filing | W5-F02 | U-073 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W5 | filing | W5-F03 | U-115 parts 1 to 3 unfiled | product | none | `ROADMAP.md`, `docs/item_notes/phase7.md`, `docs/LEDGER.md` | none | - | - | - |
| W6 | 1 | W6-G1-S1 | CS-1435 part 2 | product | none | none | none | - | v0.2.0 | - |
| W6 | 1 | W6-G1-S2 | U-073.1 unfiled | product | `clockspeed/surface/web/` `panel_play`, `tests/surface/` `test-panel_play` | `tools/provenance.tsv` | none | - | v0.3.0 | filed by W5 |
| W6 | 2 | W6-G2-S1 | CS-1435 part 3 | product | none | none | `docs/OPERATIONS.md` | - | v0.2.0 | - |
| W6 | 2 | W6-G2-S2 | U-073.4 unfiled | product | none | `tools/provenance.tsv` | none | - | v0.3.0 | filed by W5 |
| W6 | 3 | W6-G3-S1 | U-060.1 unfiled | product | none | none | none | - | v0.2.0 | filed by W5 |
| W6 | 3 | W6-G3-S2 | U-115.1 unfiled | product | none | `docs/LEDGER.md` | none | - | v0.2.0 | filed by W5 |
| W6 | filing | W6-F01 | CS-1260 child row unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W6 | lane | W6-L01 | CS-1067 | product | none | none | none | lane gap | - | - |
| W7 | 1 | W7-G1-S1 | U-073.2 unfiled | product | none | none | none | - | v0.3.0 | filed by W5 |
| W7 | 1 | W7-G1-S2 | U-060.2 unfiled | product | none | none | none | - | v0.2.0 | filed by W5 |
| W7 | 2 | W7-G2-S1 | CS-1260.1 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | none | - | - | child row filed by W6 |
| W7 | 2 | W7-G2-S2 | CS-1252.1 | product | `clockspeed/audit/` `freshness`, `tests/audit/` `test-freshness`, `tests/surface/` `test-freshness` | none | none | - | v0.3.0 | - |
| W7 | 3 | W7-G3-S1 | U-073.3 unfiled | product | none | `BACKLOG.md` | none | - | v0.3.0 | filed by W5 |
| W7 | 3 | W7-G3-S2 | CS-623 | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | - |
| W7 | filing | W7-F01 | U-061 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W7 | filing | W7-F02 | U-116 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W7 | filing | W7-F03 | U-117 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W8 | 1 | W8-G1-S1 | U-116 unfiled | product | `tests/surface/` `test-registry_provider_memo` | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | filed by W7 |
| W8 | 1 | W8-G1-S2 | CS-1260.2 | product | none | none | none | - | - | child row filed by W6 |
| W8 | 2 | W8-G2-S1 | U-117 unfiled | product | `clockspeed/surface/` `priority`, `tests/surface/` `test-priority` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | `docs/OPERATIONS.md` | - | - | filed by W7 |
| W8 | 2 | W8-G2-S2 | U-060.3 unfiled | product | none | none | none | - | v0.2.0 | filed by W5 |
| W8 | 3 | W8-G3-S1 | U-060.4 unfiled | product | none | none | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W5 |
| W8 | 3 | W8-G3-S2 | U-061.1 unfiled | product | none | none | none | - | v0.2.0 | filed by W7 |
| W8 | filing | W8-F01 | U-074 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W8 | filing | W8-F02 | U-097 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W9 | 1 | W9-G1-S1 | CS-1252.2 | product | none | none | none | - | v0.3.0 | - |
| W9 | 1 | W9-G1-S2 | U-074.1 unfiled | product | `tests/surface/` `test-panel_repaint` | `tools/provenance.tsv` | none | - | v0.3.0 | filed by W8 |
| W9 | 2 | W9-G2-S1 | U-115.2 unfiled | product | `tests/surface/` `test-world_provider_reload` | none | none | - | v0.2.0 | filed by W5 |
| W9 | 2 | W9-G2-S2 | U-097.1 unfiled | product | `shell/lib/` `guard`, `shell/test/` `guard.test` | `tools/provenance.tsv` | none | - | - | filed by W8 |
| W9 | 3 | W9-G3-S1 | CS-622 | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | - |
| W9 | 3 | W9-G3-S2 | CS-1130.1 | process | none | none | none | - | - | - |
| W9 | filing | W9-F01 | CS-1251 extension unfiled | product | none | `docs/item_notes/phase5.md`, `docs/LEDGER.md` | none | - | - | - |
| W10 | 1 | W10-G1-S1 | CS-1251.1 | product | `tests/save/` `test-settle` | `tools/provenance.tsv` | none | - | v0.3.0 | extension filed by W9 |
| W10 | 1 | W10-G1-S2 | CS-1252.3 | product | none | none | none | - | v0.3.0 | - |
| W10 | 2 | W10-G2-S1 | U-074.2 unfiled | product | none | none | none | - | v0.3.0 | filed by W8 |
| W10 | 2 | W10-G2-S2 | U-115.3 unfiled | product | `tests/surface/` `test-health_readiness` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase7.md` | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W5 |
| W10 | 3 | W10-G3-S1 | CS-621 | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | - |
| W10 | 3 | W10-G3-S2 | CS-1151 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4-followups-1000.md`, `docs/item_notes/phase4-followups.md` | none | - | - | - |
| W11 | 1 | W11-G1-S1 | U-097.2 unfiled | product | none | none | none | - | - | filed by W8 |
| W11 | 1 | W11-G1-S2 | CS-1251.2 | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md` | none | - | v0.3.0 | extension filed by W9 |
| W11 | 2 | W11-G2-S1 | CS-1252.4 | product | none | `ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/item_notes/phase5.md`, `tools/provenance.tsv` | none | - | v0.3.0 | - |
| W11 | 2 | W11-G2-S2 | U-074.3 unfiled | product | none | none | none | - | v0.3.0 | filed by W8 |
| W11 | 3 | W11-G3-S1 | U-097.3 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | none | - | - | filed by W8 |
| W11 | 3 | W11-G3-S2 | CS-607 | process | none | none | none | - | - | - |
| W11 | filing | W11-F01 | U-059 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W11 | filing | W11-F02 | U-098 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W11 | filing | W11-F03 | U-115 part 4 unfiled | product | none | `ROADMAP.md`, `docs/item_notes/phase7.md`, `docs/LEDGER.md` | none | - | - | - |
| W12 | 1 | W12-G1-S1 | U-115.4 unfiled | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase7.md` | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W11 |
| W12 | 1 | W12-G1-S2 | U-061.2 unfiled | product | none | none | none | - | v0.2.0 | filed by W7 |
| W12 | 2 | W12-G2-S1 | CS-1432 part 1 | product | none | `docs/LEDGER.md` | none | - | v0.3.0 | - |
| W12 | 2 | W12-G2-S2 | U-098.1 unfiled | product | none | none | none | - | - | filed by W11 |
| W12 | 3 | W12-G3-S1 | U-098.2 unfiled | product | none | none | none | - | - | filed by W11 |
| W12 | 3 | W12-G3-S2 | U-059.1 unfiled | product | `clockspeed/surface/` `owner`, `tests/surface/` `test-owner` | `tools/provenance.tsv` | none | - | - | filed by W11 |
| W12 | filing | W12-F01 | U-101 unfiled | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W12 | filing | W12-F02 | U-119 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W13 | 1 | W13-G1-S1 | CS-1432 part 2 | product | `clockspeed/surface/` `watch`, `tests/surface/` `test-watch` | none | none | - | v0.3.0 | - |
| W13 | 1 | W13-G1-S2 | U-119 unfiled | product | `tests/surface/` `test-start_purge` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | `docs/OPERATIONS.md` | - | - | filed by W12 |
| W13 | 2 | W13-G2-S1 | CS-1432 part 3 | product | `clockspeed/surface/api/` `events`, `tests/surface/` `test-events` | none | none | - | v0.3.0 | - |
| W13 | 2 | W13-G2-S2 | U-101.1 unfiled | process | `config/` `runtime_pins`, `tests/` `test-runtime_pins` | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W12 |
| W13 | 3 | W13-G3-S1 | CS-1432 part 4 | product | none | none | none | - | v0.3.0 | - |
| W13 | 3 | W13-G3-S2 | CS-1142 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-1000.md` | none | - | - | - |
| W13 | filing | W13-F01 | U-002 unfiled | process | none | `ROADMAP.md`, `docs/item_notes/phase7.md`, `docs/LEDGER.md` | none | - | - | - |
| W13 | filing | W13-F02 | U-091 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W13 | filing | W13-F03 | CS-1258 extension unfiled | product | none | `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W13 | lane | W13-L01 | CS-603 | process | none | none | none | lane gap | - | - |
| W14 | 1 | W14-G1-S1 | U-098.3 unfiled | product | none | none | none | - | - | filed by W11 |
| W14 | 1 | W14-G1-S2 | U-002.1 unfiled | process | `installer/__init__`, `installer/manifest`, `tests/` `installer/test-manifest`, `tools/` `release_build`, `tests/` `packaging/test-release_build`, `tests/` `installer/__init__`, `tests/` `packaging/__init__` | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W13 |
| W14 | 2 | W14-G2-S1 | U-091.1 unfiled | product | none | none | none | - | v0.2.0 | filed by W13 |
| W14 | 2 | W14-G2-S2 | U-098.4 unfiled | product | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | `docs/OPERATIONS.md` | - | - | filed by W11 |
| W14 | 3 | W14-G3-S1 | U-098.5 unfiled | product | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | `docs/OPERATIONS.md` | - | - | filed by W11 |
| W14 | 3 | W14-G3-S2 | CS-1258.1 | product | none | none | none | - | - | extension filed by W13 |
| W15 | 1 | W15-G1-S1 | CS-1432 part 5 | product | `tests/surface/` `test-freshness_strip` | none | none | - | v0.3.0 | - |
| W15 | 1 | W15-G1-S2 | U-002.2 unfiled | process | `tests/` `packaging/test-artifact_contents`, `tests/` `packaging/test-artifact_boot` | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W13 |
| W15 | 2 | W15-G2-S1 | U-091.2 unfiled | product | `shell/lib/` `mint`, `shell/test/` `mint.test` | none | none | - | v0.2.0 | filed by W13 |
| W15 | 2 | W15-G2-S2 | U-101.2 unfiled | process | `tools/` `runtime_pins` | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W12 |
| W15 | 3 | W15-G3-S1 | U-002.3 unfiled | process | `tests/` `test-version_owner` | `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `tools/provenance.tsv` | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W13 |
| W15 | 3 | W15-G3-S2 | CS-608 | process | none | none | none | - | - | - |
| W15 | filing | W15-F01 | U-102 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W16 | 1 | W16-G1-S1 | CS-619.2 | process | none | none | none | - | - | - |
| W16 | 1 | W16-G1-S2 | CS-1432 part 6 | product | none | none | none | - | v0.3.0 | - |
| W16 | 2 | W16-G2-S1 | U-091.3 unfiled | product | `docs/adr/` `NNNN-certificate-lifecycle-and-the-per-start-token` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/adr/README.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W13 |
| W16 | 2 | W16-G2-S2 | U-101.3 unfiled | process | `docs/adr/` `NNNN-runtime-pins` | `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/adr/README.md`, `tools/provenance.tsv` | none | - | v0.2.0 | filed by W12 |
| W16 | 3 | W16-G3-S1 | U-102.1 unfiled | product | `installer/__main__`, `installer/cli`, `tests/` `installer/test-cli` | `docs/LEDGER.md`, `tools/provenance.tsv` | none | - | v0.2.0 | filed by W15 |
| W16 | 3 | W16-G3-S2 | CS-1258.2 | product | none | none | none | - | - | extension filed by W13 |
| W16 | filing | W16-F01 | U-099 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W16 | lane | W16-L01 | CS-468 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | lane gap | - | - |
| W17 | 1 | W17-G1-S1 | CS-619.3 | process | `shell/lib/` `wiring`, `shell/test/` `wiring.test` | `tools/provenance.tsv` | none | - | - | - |
| W17 | 1 | W17-G1-S2 | CS-1432 part 7 | product | `tests/surface/` `test-event_focus` | `docs/LEDGER.md` | `docs/hud_doctrine.md` | - | v0.3.0 | - |
| W17 | 2 | W17-G2-S1 | CS-619.4 | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | - |
| W17 | 2 | W17-G2-S2 | CS-1432 part 8 | product | none | `ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md`, `docs/item_notes/phase6.md` | none | - | v0.3.0 | - |
| W17 | 3 | W17-G3-S1 | U-099.1 unfiled | product | `installer/fuses`, `tests/` `installer/test-fuses` | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W16 |
| W17 | 3 | W17-G3-S2 | U-102.7 unfiled | product | none | `docs/LEDGER.md`, `tools/provenance.tsv` | none | - | v0.2.0 | filed by W15 |
| W18 | 1 | W18-G1-S1 | U-159 not filed | product | none | none | none | - | - | - |
| W18 | 1 | W18-G1-S2 | U-099.2 unfiled | product | none | none | none | - | v0.2.0 | filed by W16 |
| W18 | 2 | W18-G2-S1 | U-102.2 unfiled | product | `installer/paths`, `tests/` `installer/test-paths`, `installer/marker`, `tests/` `installer/test-marker` | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W15 |
| W18 | 2 | W18-G2-S2 | U-059.2 unfiled | product | none | none | none | - | - | filed by W11 |
| W18 | 3 | W18-G3-S1 | CS-612 | process | none | none | none | - | - | - |
| W18 | 3 | W18-G3-S2 | CS-464 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | - | - | - |
| W19 | 1 | W19-G1-S1 | U-102.3 unfiled | product | `installer/runtimes`, `tests/` `installer/test-runtimes`, `installer/engine`, `tests/` `installer/test-engine` | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W15 |
| W19 | 1 | W19-G1-S2 | U-059.3 unfiled | product | `tests/shell/` `test-owner_pipe` | `tools/provenance.tsv` | none | - | - | filed by W11 |
| W19 | 2 | W19-G2-S1 | U-102.4 unfiled | product | `installer/selftest`, `tests/` `installer/test-selftest`, `installer/report`, `tests/` `installer/test-report` | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W15 |
| W19 | 2 | W19-G2-S2 | U-059.4 unfiled | product | `docs/adr/` `NNNN-the-shell-supervises-for-the-whole-session` | `docs/adr/README.md`, `tools/provenance.tsv` | `docs/OPERATIONS.md` | - | - | filed by W11 |
| W19 | 3 | W19-G3-S1 | CS-876 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-850.md` | none | - | - | - |
| W19 | 3 | W19-G3-S2 | CS-457 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | - | - | - |
| W19 | filing | W19-F01 | U-062 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W19 | filing | W19-F02 | U-134 unfiled | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W19 | filing | W19-F03 | U-149 unfiled | process | none | `ROADMAP.md`, `docs/item_notes/phase7.md`, `docs/LEDGER.md` | none | - | - | - |
| W20 | 1 | W20-G1-S1 | U-134 unfiled | process | `tools/` `release_notes`, `tests/` `test-release_notes` | `BACKLOG.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `tools/provenance.tsv` | none | - | v0.2.0 | filed by W19 |
| W20 | 1 | W20-G1-S2 | U-102.5 unfiled | product | `installer/bootstrap/install`, `installer/bootstrap/install`, `installer/bootstrap/mint`, `installer/mint`, `tests/` `installer/test-mint`, `tests/` `installer/test-bootstrap_text` | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W15 |
| W20 | 2 | W20-G2-S1 | U-102.8 unfiled | product | none | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W15 |
| W20 | 2 | W20-G2-S2 | U-062.1 unfiled | product | none | none | none | - | v0.2.0 | filed by W19 |
| W20 | 3 | W20-G3-S1 | CS-1436 part 2 | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | - |
| W20 | 3 | W20-G3-S2 | CS-1430 | product | `clockspeed/progress/` `delta`, `tests/progress/` `test-delta` | `docs/ARCHITECTURE.md`, `tools/provenance.tsv` | none | - | - | - |
| W20 | filing | W20-F01 | U-125 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W20 | filing | W20-F02 | U-132 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W20 | filing | W20-F03 | CS-1398 extension unfiled | product | none | `docs/item_notes/phase5.md`, `docs/LEDGER.md` | none | - | - | - |
| W20 | lane | W20-L01 | CS-808 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups.md` | none | lane gap | - | - |
| W21 | 1 | W21-G1-S1 | U-102.6 unfiled | product | `docs/adr/` `NNNN-the-installer` | `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/adr/README.md`, `tools/provenance.tsv` | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W15 |
| W21 | 1 | W21-G1-S2 | CS-1248.2 | product | none | none | none | - | - | - |
| W21 | 2 | W21-G2-S1 | U-132.1 unfiled | product | `shell/lib/` `launch`, `shell/test/` `launch.test`, `shell/` `launcher/main` | none | none | - | v0.2.0 | filed by W20 |
| W21 | 2 | W21-G2-S2 | CS-1398.1 | product | none | `config/lane_scopes.json`, `docs/item_notes/phase5.md` | none | - | - | extension filed by W20 |
| W21 | 3 | W21-G3-S1 | U-125.1 unfiled | product | `clockspeed/surface/` `oplog`, `tests/surface/` `test-oplog` | `tools/provenance.tsv` | none | - | - | filed by W20 |
| W21 | 3 | W21-G3-S2 | CS-916.1 | product | none | none | none | - | - | - |
| W22 | 1 | W22-G1-S1 | U-132.2 unfiled | product | `shell/` `launcher/package` | none | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W20 |
| W22 | 1 | W22-G1-S2 | U-062.2 unfiled | product | `shell/lib/` `lifecycle`, `shell/test/` `lifecycle.test` | none | none | - | v0.2.0 | filed by W19 |
| W22 | 2 | W22-G2-S1 | U-132.3 unfiled | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | v0.2.0 | filed by W20 |
| W22 | 2 | W22-G2-S2 | CS-1248.3 | product | none | none | none | - | - | - |
| W22 | 3 | W22-G3-S1 | U-099.3 unfiled | product | none | `BACKLOG.md`, `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | `docs/OPERATIONS.md` | - | - | filed by W16 |
| W22 | 3 | W22-G3-S2 | CS-609 | process | none | none | none | - | - | - |
| W22 | filing | W22-F01 | U-133 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W23 | 1 | W23-G1-S1 | U-133.1 unfiled | product | `installer/shellint`, `tests/` `installer/test-shellint`, `installer/procs`, `tests/` `installer/test-procs` | none | none | - | v0.2.0 | filed by W22 |
| W23 | 1 | W23-G1-S2 | U-062.3 unfiled | product | none | `docs/adr/README.md` | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W19 |
| W23 | 2 | W23-G2-S1 | U-133.2 unfiled | product | `installer/uninstall`, `tests/` `installer/test-uninstall`, `installer/recycle` | none | none | - | v0.2.0 | filed by W22 |
| W23 | 2 | W23-G2-S2 | CS-1046.1 | product | `clockspeed/surface/api/` `audit`, `tests/surface/` `test-audit`, `clockspeed/surface/api/` `plan`, `tests/surface/` `test-plan` | `tools/provenance.tsv` | none | - | v0.4.0 | - |
| W23 | 3 | W23-G3-S1 | CS-611 | process | none | `docs/item_notes/phase6.md` | none | - | - | - |
| W23 | 3 | W23-G3-S2 | CS-620 | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | `docs/OPERATIONS.md` | - | - | - |
| W23 | filing | W23-F01 | U-126 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W23 | lane | W23-L01 | CS-465 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | lane gap | - | - |
| W24 | 1 | W24-G1-S1 | CS-1248.4 | product | none | none | none | - | - | - |
| W24 | 1 | W24-G1-S2 | U-126 unfiled | product | none | none | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W23 |
| W24 | 2 | W24-G2-S1 | U-133.3 unfiled | product | none | `docs/LEDGER.md` | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W22 |
| W24 | 2 | W24-G2-S2 | CS-1046.2 | product | none | none | none | - | v0.4.0 | - |
| W24 | 3 | W24-G3-S1 | CS-1046.3 | product | none | none | none | - | v0.4.0 | - |
| W24 | 3 | W24-G3-S2 | CS-915 | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | - |
| W24 | filing | W24-F01 | U-004 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W25 | 1 | W25-G1-S1 | CS-1248.5 | product | none | none | none | - | - | - |
| W25 | 1 | W25-G1-S2 | U-004.1 unfiled | product | `installer/update`, `tests/` `installer/test-update`, `installer/net`, `tests/` `packaging/test-update_requests` | `tools/provenance.tsv` | none | - | v0.2.0 | filed by W24 |
| W25 | 2 | W25-G2-S1 | CS-1248.6 | product | none | none | none | - | - | - |
| W25 | 2 | W25-G2-S2 | U-004.2 unfiled | product | none | none | none | - | v0.2.0 | filed by W24 |
| W25 | 3 | W25-G3-S1 | CS-1046.4 | product | none | `ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | v0.4.0 | - |
| W25 | 3 | W25-G3-S2 | CS-467 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | - | - | - |
| W25 | filing | W25-F01 | U-104 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W25 | filing | W25-F02 | U-118 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W26 | 1 | W26-G1-S1 | CS-1065 | product | none | none | none | - | - | - |
| W26 | 1 | W26-G1-S2 | CS-1248.7 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md`, `tools/provenance.tsv` | none | - | - | - |
| W26 | 2 | W26-G2-S1 | U-004.3 unfiled | product | none | `docs/LEDGER.md` | none | - | v0.2.0 | filed by W24 |
| W26 | 2 | W26-G2-S2 | CS-1256.1 | product | none | none | none | - | - | - |
| W26 | 3 | W26-G3-S1 | U-104 unfiled | product | none | `docs/GATED.md`, `docs/LEDGER.md` | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W25 |
| W26 | 3 | W26-G3-S2 | U-118.1 unfiled | product | `tests/advisor/` `test-advise_memo` | `ROADMAP.md`, `docs/item_notes/phase6.md`, `tools/provenance.tsv` | none | - | - | filed by W25 |
| W26 | filing | W26-F01 | U-135 unfiled | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W26 | filing | W26-F02 | U-136 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W26 | lane | W26-L01 | CS-483 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4.md` | none | lane gap | - | - |
| W27 | 1 | W27-G1-S1 | U-135.1 unfiled | process | `tools/` `release_stage`, `tests/` `test-release_stage` | none | none | - | v0.2.0 | filed by W26 |
| W27 | 1 | W27-G1-S2 | CS-1256.2 | product | none | none | none | - | - | - |
| W27 | 2 | W27-G2-S1 | U-135.2 unfiled | process | `.github/workflows/` `release`, `tests/` `test-release_workflow` | none | none | - | v0.2.0 | filed by W26 |
| W27 | 2 | W27-G2-S2 | U-136.1 unfiled | product | `installer/migrate`, `tests/` `installer/test-migrate` | none | none | - | v0.2.0 | filed by W26 |
| W27 | 3 | W27-G3-S1 | U-135.3 unfiled | process | none | none | none | - | v0.2.0 | filed by W26 |
| W27 | 3 | W27-G3-S2 | U-136.2 unfiled | product | `tests/` `installer/test-first_run` | `docs/LEDGER.md` | `docs/OPERATIONS.md` | - | v0.2.0 | filed by W26 |
| W27 | filing | W27-F01 | U-103 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W28 | 1 | W28-G1-S1 | U-118.2 unfiled | product | none | none | none | - | - | filed by W25 |
| W28 | 1 | W28-G1-S2 | CS-1256.3 | product | `tests/surface/` `test-numeric_schema` | none | none | - | - | - |
| W28 | 2 | W28-G2-S1 | U-103 unfiled | product | none | `THIRD_PARTY.md`, `docs/LEDGER.md` | none | - | v0.2.0 | filed by W27 |
| W28 | 2 | W28-G2-S2 | U-118.3 unfiled | product | none | none | none | - | - | filed by W25 |
| W28 | 3 | W28-G3-S1 | CS-1256.4 | product | none | `tools/provenance.tsv` | none | - | - | - |
| W28 | 3 | W28-G3-S2 | U-118.4 unfiled | product | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | none | - | - | filed by W25 |
| W28 | filing | W28-F01 | CS-1257 extension unfiled | product | none | `ROADMAP.md`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W29 | 1 | W29-G1-S1 | CS-1420 part 1 | product | none | none | none | - | - | - |
| W29 | 1 | W29-G1-S2 | CS-1257.1 | product | none | `docs/LEDGER.md` | none | - | v0.3.0 | extension filed by W28 |
| W29 | 2 | W29-G2-S1 | CS-1420 part 2 | product | `clockspeed/solve/` `staging`, `tests/solve/` `test-staging` | none | none | - | - | - |
| W29 | 2 | W29-G2-S2 | CS-1257.2 | product | `tests/advisor/` `test-standing_statement` | none | none | - | v0.3.0 | extension filed by W28 |
| W29 | 3 | W29-G3-S1 | CS-1420 part 3 | product | none | none | none | - | - | - |
| W29 | 3 | W29-G3-S2 | CS-1257.3 | product | none | none | none | - | v0.3.0 | extension filed by W28 |
| W29 | filing | W29-F01 | CS-962 child row unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase4-followups-960.md`, `docs/LEDGER.md` | none | - | - | - |
| W30 | 1 | W30-G1-S1 | CS-1420 part 4 | product | none | none | none | - | - | - |
| W30 | 1 | W30-G1-S2 | CS-962.1 | product | none | none | none | - | v0.3.0 | child row filed by W29 |
| W30 | 2 | W30-G2-S1 | CS-1257.4 | product | none | none | none | - | v0.3.0 | extension filed by W28 |
| W30 | 2 | W30-G2-S2 | CS-1420 part 5 | product | none | none | none | - | - | - |
| W30 | 3 | W30-G3-S1 | CS-1257.11 | product | `tests/surface/` `test-standing_memo` | `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | none | - | v0.3.0 | extension filed by W28 |
| W30 | 3 | W30-G3-S2 | CS-1420 part 6 | product | none | none | none | - | - | - |
| W30 | filing | W30-F01 | U-079 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W30 | lane | W30-L01 | CS-849 | process | `tests/` `test-work_directory_left_absent` | `tools/provenance.tsv` | none | lane gap | - | - |
| W31 | 1 | W31-G1-S1 | CS-962.2 | product | `clockspeed/surface/web/` `panel_console`, `tests/surface/` `test-panel_console` | `tools/provenance.tsv` | none | - | v0.3.0 | child row filed by W29 |
| W31 | 1 | W31-G1-S2 | CS-1426 part 1 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase5.md` | none | - | - | - |
| W31 | 2 | W31-G2-S1 | CS-962.3 | product | none | `BACKLOG.md`, `tools/provenance.tsv` | none | - | v0.3.0 | child row filed by W29 |
| W31 | 2 | W31-G2-S2 | CS-1420 part 7 | product | none | none | none | - | - | - |
| W31 | 3 | W31-G3-S1 | U-079.1 unfiled | product | none | `docs/item_notes/phase6.md` | none | - | - | filed by W30 |
| W31 | 3 | W31-G3-S2 | CS-843.1 | product | none | none | none | - | - | - |
| W31 | filing | W31-F01 | U-063 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W32 | 1 | W32-G1-S1 | CS-962.4 | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-960.md`, `tools/provenance.tsv` | none | - | v0.3.0 | child row filed by W29 |
| W32 | 1 | W32-G1-S2 | CS-1426 part 2 | product | none | none | none | - | - | - |
| W32 | 2 | W32-G2-S1 | U-063 unfiled | product | `shell/lib/` `login`, `shell/test/` `login.test` | none | `docs/OPERATIONS.md` | - | - | filed by W31 |
| W32 | 2 | W32-G2-S2 | CS-1420 part 8 | product | none | none | none | - | - | - |
| W32 | 3 | W32-G3-S1 | CS-1420 part 9 | product | none | none | none | - | - | - |
| W32 | 3 | W32-G3-S2 | CS-1258.3 | product | none | none | none | - | - | extension filed by W13 |
| W33 | 1 | W33-G1-S1 | CS-1429 part 1 | product | none | `docs/LEDGER.md` | none | - | v0.3.0 | - |
| W33 | 1 | W33-G1-S2 | CS-1420 part 10 | product | none | `ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/item_notes/phase5.md`, `tools/provenance.tsv` | none | - | - | - |
| W33 | 2 | W33-G2-S1 | CS-1398.2 | product | none | none | none | - | - | extension filed by W20 |
| W33 | 2 | W33-G2-S2 | CS-1429 part 2 | product | none | none | none | - | v0.3.0 | - |
| W33 | 3 | W33-G3-S1 | CS-1398.3 | product | none | none | none | - | - | extension filed by W20 |
| W33 | 3 | W33-G3-S2 | CS-1429 part 3 | product | none | `docs/item_notes/phase5.md` | `BOOTSTRAP.md` | - | v0.3.0 | - |
| W33 | filing | W33-F01 | U-075 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W33 | filing | W33-F02 | CS-1064 extension unfiled | product | none | `docs/item_notes/phase5.md`, `docs/LEDGER.md` | none | - | - | - |
| W33 | filing | W33-F03 | CS-1254 extension unfiled | product | none | `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W33 | lane | W33-L01 | CS-474 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | lane gap | - | - |
| W34 | 1 | W34-G1-S1 | CS-1254.1 | product | `clockspeed/progress/` `coverage`, `tests/progress/` `test-coverage` | `tools/provenance.tsv` | none | - | - | extension filed by W33 |
| W34 | 1 | W34-G1-S2 | CS-1398.4 | product | none | none | none | - | - | extension filed by W20 |
| W34 | 2 | W34-G2-S1 | U-075.1 unfiled | product | none | none | none | - | v0.3.0 | filed by W33 |
| W34 | 2 | W34-G2-S2 | CS-1254.2 | product | none | none | none | - | - | extension filed by W33 |
| W34 | 3 | W34-G3-S1 | CS-1398.5 | product | `docs/adr/` `NNNN-cs-1398-SLUG` | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/adr/README.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md` | none | - | - | extension filed by W20 |
| W34 | 3 | W34-G3-S2 | CS-1064.1 | product | none | none | none | - | - | extension filed by W33 |
| W34 | filing | W34-F01 | CS-1236 extension unfiled | product | none | `docs/item_notes/phase5.md`, `docs/LEDGER.md` | none | - | - | - |
| W35 | 1 | W35-G1-S1 | CS-1254.3 | product | `tests/advisor/` `test-plan_adopt_built` | `tools/provenance.tsv` | none | - | - | extension filed by W33 |
| W35 | 1 | W35-G1-S2 | CS-1064.2 | product | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md` | none | - | - | extension filed by W33 |
| W35 | 2 | W35-G2-S1 | CS-1254.4 | product | none | none | none | - | - | extension filed by W33 |
| W35 | 2 | W35-G2-S2 | CS-1422 part 1 | product | none | none | none | - | - | - |
| W35 | 3 | W35-G3-S1 | CS-1254.5 | product | none | none | none | - | - | extension filed by W33 |
| W35 | 3 | W35-G3-S2 | CS-1236.1 | product | `clockspeed/surface/api/` `overlay`, `tests/surface/` `test-overlay` | none | none | - | v0.4.0 | extension filed by W34 |
| W35 | filing | W35-F01 | U-003 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W36 | 1 | W36-G1-S1 | CS-1254.6 | product | `tests/advisor/` `test-plan_built` | `tools/provenance.tsv` | none | - | - | extension filed by W33 |
| W36 | 1 | W36-G1-S2 | CS-1258.4 | product | `tools/` `a11y_rules`, `tests/` `test-a11y_rules` | `tools/provenance.tsv` | none | - | - | extension filed by W13 |
| W36 | 2 | W36-G2-S1 | CS-1254.7 | product | none | `docs/ARCHITECTURE.md` | none | - | - | extension filed by W33 |
| W36 | 2 | W36-G2-S2 | CS-1258.5 | product | none | none | none | - | - | extension filed by W13 |
| W36 | 3 | W36-G3-S1 | U-075.2 unfiled | product | none | `docs/item_notes/phase4-followups-960.md` | none | - | v0.3.0 | filed by W33 |
| W36 | 3 | W36-G3-S2 | U-003.1 unfiled | product | `docs/adr/` `NNNN-the-overlay-capability-boundary` | `docs/adr/README.md`, `tools/provenance.tsv` | none | - | v0.5.0 | filed by W35 |
| W36 | lane | W36-L01 | CS-613 | process | none | none | none | lane gap | - | - |
| W37 | 1 | W37-G1-S1 | CS-1421 | product | none | none | none | - | - | - |
| W37 | 1 | W37-G1-S2 | CS-1258.7 | product | none | none | none | - | - | extension filed by W13 |
| W37 | 2 | W37-G2-S1 | CS-1422 part 2 | product | none | none | none | - | - | - |
| W37 | 2 | W37-G2-S2 | CS-1258.8 | product | `tests/surface/` `test-panel_a11y_rules` | `tools/provenance.tsv` | none | - | - | extension filed by W13 |
| W37 | 3 | W37-G3-S1 | CS-1051 | process | none | none | none | - | - | - |
| W37 | 3 | W37-G3-S2 | CS-616 | process | none | `docs/item_notes/phase6.md` | none | - | - | - |
| W37 | filing | W37-F01 | U-054 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W37 | filing | W37-F02 | U-056 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W38 | 1 | W38-G1-S1 | CS-1422 part 3 | product | `tests/advisor/` `test-plan_power` | `BACKLOG.md`, `tools/provenance.tsv` | none | - | - | - |
| W38 | 1 | W38-G1-S2 | U-054 unfiled | product | `clockspeed/surface/web/` `panel_balance`, `tests/surface/` `test-panel_balance`, `clockspeed/audit/` `shortlist`, `tests/audit/` `test-shortlist` | `docs/item_notes/phase6.md` | none | - | v0.4.0 | filed by W37 |
| W38 | 2 | W38-G2-S1 | CS-1236.5 | product | `tests/advisor/` `test-overlay_trace` | none | none | - | v0.4.0 | extension filed by W34 |
| W38 | 2 | W38-G2-S2 | U-056.1 unfiled | product | none | none | none | - | - | filed by W37 |
| W38 | 3 | W38-G3-S1 | CS-1236.2 | product | none | none | none | - | v0.4.0 | extension filed by W34 |
| W38 | 3 | W38-G3-S2 | CS-877 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-850.md` | none | - | - | - |
| W38 | filing | W38-F01 | U-012 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W38 | filing | W38-F02 | U-064 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W39 | 1 | W39-G1-S1 | CS-1236.3 | product | none | none | `BOOTSTRAP.md` | - | v0.4.0 | extension filed by W34 |
| W39 | 1 | W39-G1-S2 | U-012.1 unfiled | product | `clockspeed/advisor/` `glance`, `tests/advisor/` `test-glance` | `tools/provenance.tsv` | none | - | v0.5.0 | filed by W38 |
| W39 | 2 | W39-G2-S1 | CS-1236.6 | product | `tests/advisor/` `test-plan_preview` | none | none | - | v0.4.0 | extension filed by W34 |
| W39 | 2 | W39-G2-S2 | U-056.2 unfiled | product | none | none | none | - | - | filed by W37 |
| W39 | 3 | W39-G3-S1 | CS-1236.7 | product | none | none | none | - | v0.4.0 | extension filed by W34 |
| W39 | 3 | W39-G3-S2 | U-064.1 unfiled | product | none | none | none | - | - | filed by W38 |
| W39 | filing | W39-F01 | U-010 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W40 | 1 | W40-G1-S1 | CS-1236.8 | product | none | none | none | - | v0.4.0 | extension filed by W34 |
| W40 | 1 | W40-G1-S2 | U-010 unfiled | product | none | `ROADMAP.md`, `docs/GATED.md`, `docs/LEDGER.md` | `docs/hud_doctrine.md` | - | v0.5.0 | filed by W39 |
| W40 | 2 | W40-G2-S1 | U-012.2 unfiled | product | `clockspeed/surface/api/` `glance`, `tests/surface/` `test-glance_route` | `docs/ARCHITECTURE.md`, `tools/provenance.tsv` | `BOOTSTRAP.md` | - | v0.5.0 | filed by W38 |
| W40 | 2 | W40-G2-S2 | CS-1243.1 | product | `clockspeed/audit/` `siting`, `tests/audit/` `test-siting` | `tools/provenance.tsv` | none | - | - | - |
| W40 | 3 | W40-G3-S1 | CS-1048.4 | product | none | none | none | - | - | extension filed by W2 |
| W40 | filing | W40-F01 | U-057 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W40 | lane | W40-L01 | CS-1001 | process | none | none | none | lane gap | - | - |
| W41 | 1 | W41-G1-S1 | U-012.3 unfiled | product | none | none | `docs/hud_doctrine.md` | - | v0.5.0 | filed by W38 |
| W41 | 1 | W41-G1-S2 | CS-1048.5 | product | none | none | none | - | - | extension filed by W2 |
| W41 | 2 | W41-G2-S1 | U-057.1 unfiled | product | none | none | none | - | - | filed by W40 |
| W41 | 2 | W41-G2-S2 | CS-1249.1 | product | none | `config/lane_scopes.json` | none | - | - | - |
| W41 | 3 | W41-G3-S1 | U-057.2 unfiled | product | none | none | `docs/OPERATIONS.md` | - | - | filed by W40 |
| W41 | 3 | W41-G3-S2 | CS-1048.3 | product | `clockspeed/audit/` `labels`, `tests/audit/` `test-labels` | none | none | - | - | extension filed by W2 |
| W41 | filing | W41-F01 | U-109 unfiled | process | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W42 | 1 | W42-G1-S1 | CS-1243.2 | product | `clockspeed/advisor/rules/` `siting`, `tests/advisor/rules/` `test-siting` | `tools/provenance.tsv` | none | - | - | - |
| W42 | 1 | W42-G1-S2 | CS-1048.6 | product | none | `BACKLOG.md`, `ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md`, `tools/provenance.tsv` | none | - | - | extension filed by W2 |
| W42 | 2 | W42-G2-S1 | CS-1243.3 | product | none | none | none | - | - | - |
| W42 | 2 | W42-G2-S2 | U-109 unfiled | process | `clockspeed/audit/` `extraction`, `tests/audit/` `test-extraction` | `BACKLOG.md` | none | - | - | filed by W41 |
| W42 | 3 | W42-G3-S1 | CS-1249.2 | product | `tests/solve/` `test-cycles` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md`, `tools/provenance.tsv` | none | - | - | - |
| W42 | 3 | W42-G3-S2 | CS-440.1 | product | none | none | none | - | - | - |
| W42 | filing | W42-F01 | CS-872 extension unfiled | product | none | `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W42 | filing | W42-F02 | CS-1047 child row A unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | after the CS-1047 doc slice (returned, unowned) |
| W42 | filing | W42-F03 | CS-1047 child row B unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | after the CS-1047 doc slice (returned, unowned) |
| W43 | 1 | W43-G1-S1 | CS-1047.8 | product | none | none | none | - | - | child row filed by W42 |
| W43 | 1 | W43-G1-S2 | CS-872.1 | product | none | none | `docs/OPERATIONS.md` | - | - | extension filed by W42 |
| W43 | 2 | W43-G2-S1 | CS-1047.3 | product | none | none | none | - | - | child row filed by W42 |
| W43 | 2 | W43-G2-S2 | CS-1250 | product | `tests/audit/` `test-count_once` | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md`, `tools/provenance.tsv` | none | - | - | - |
| W43 | 3 | W43-G3-S1 | U-079.2 unfiled | product | none | `docs/item_notes/phase6.md` | none | - | - | filed by W30 |
| W43 | 3 | W43-G3-S2 | CS-440.2 | product | none | none | none | - | - | - |
| W43 | lane | W43-L01 | CS-1003 | process | none | none | none | lane gap | - | - |
| W44 | 1 | W44-G1-S1 | CS-1047.5 | product | none | none | none | - | - | child row filed by W42 |
| W44 | 1 | W44-G1-S2 | CS-1425 part 1 | product | `clockspeed/advisor/rules/` `production`, `tests/advisor/rules/` `test-production` | none | none | - | - | - |
| W44 | 2 | W44-G2-S1 | CS-1047.4 | product | none | none | none | - | - | child row filed by W42 |
| W44 | 2 | W44-G2-S2 | CS-1428 part 1 | product | none | none | `BOOTSTRAP.md` | - | - | - |
| W44 | 3 | W44-G3-S1 | U-077.2 unfiled | process | none | none | none | - | - | filed by W4 |
| W45 | 1 | W45-G1-S1 | CS-1047.6 | product | `clockspeed/surface/web/` `panel_plan`, `tests/surface/` `test-panel_plan` | `tools/provenance.tsv` | none | - | - | child row filed by W42 |
| W45 | 1 | W45-G1-S2 | CS-872.2 | product | `tests/surface/` `test-shortcuts` | `ROADMAP.md`, `config/lane_scopes.json`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md`, `tools/provenance.tsv` | none | - | - | extension filed by W42 |
| W45 | 2 | W45-G2-S1 | CS-1047.7 | product | `clockspeed/surface/web/` `panel_world_power`, `tests/surface/` `test-panel_world_power` | `tools/provenance.tsv` | none | - | - | child row filed by W42 |
| W45 | 2 | W45-G2-S2 | CS-1254.8 | product | none | `tools/provenance.tsv` | none | - | - | extension filed by W33 |
| W45 | 3 | W45-G3-S1 | CS-1047.1 | product | none | none | none | - | - | child row filed by W42 |
| W45 | 3 | W45-G3-S2 | CS-1425 part 2 | product | none | none | none | - | - | - |
| W45 | filing | W45-F01 | U-078 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W46 | 1 | W46-G1-S1 | CS-1047.2 | product | none | none | none | - | - | child row filed by W42 |
| W46 | 1 | W46-G1-S2 | CS-1425 part 3 | product | none | none | none | - | - | - |
| W46 | 2 | W46-G2-S1 | CS-1047.9 | product | none | none | none | - | - | child row filed by W42 |
| W46 | 2 | W46-G2-S2 | U-078.1 unfiled | product | none | none | none | - | - | filed by W45 |
| W46 | 3 | W46-G3-S1 | CS-1047.10 | product | none | `docs/item_notes/phase6.md`, `tools/provenance.tsv` | none | - | - | child row filed by W42 |
| W46 | 3 | W46-G3-S2 | CS-1425 part 4 | product | none | `ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md` | none | - | - | - |
| W46 | lane | W46-L01 | CS-1076 | process | none | none | none | lane gap | - | - |
| W47 | 1 | W47-G1-S1 | U-078.2 unfiled | product | none | none | none | - | - | filed by W45 |
| W47 | 1 | W47-G1-S2 | CS-1058.1 | product | `tests/audit/` `test-network_edges`, `tests/audit/` `test-network_library` | none | none | - | - | extension filed by W3; child row filed by W3 |
| W47 | 2 | W47-G2-S1 | CS-1428 part 2 | product | none | none | none | - | - | - |
| W47 | 2 | W47-G2-S2 | CS-1433 part 1 | product | `clockspeed/advisor/rules/` `materials`, `tests/advisor/rules/` `test-materials` | none | none | - | - | - |
| W47 | 3 | W47-G3-S1 | CS-1058.2 | product | none | none | none | - | - | extension filed by W3; child row filed by W3 |
| W47 | 3 | W47-G3-S2 | U-125.2 unfiled | product | `tests/surface/` `test-oplog_redaction` | `tools/provenance.tsv` | none | - | - | filed by W20 |
| W47 | filing | W47-F01 | U-022 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W48 | 1 | W48-G1-S1 | U-078.3 unfiled | product | none | `BACKLOG.md`, `docs/item_notes/phase6.md` | none | - | - | filed by W45 |
| W48 | 1 | W48-G1-S2 | U-022.1 unfiled | product | `clockspeed/solve/` `presets`, `tests/solve/` `test-presets` | `docs/ARCHITECTURE.md`, `tools/provenance.tsv` | none | - | - | filed by W47 |
| W48 | 2 | W48-G2-S1 | CS-1428 part 3 | product | none | none | none | - | - | - |
| W48 | 2 | W48-G2-S2 | CS-1427 part 1 | product | `clockspeed/solve/` `haul`, `tests/solve/` `test-haul` | `tools/provenance.tsv` | none | - | - | - |
| W48 | 3 | W48-G3-S1 | U-125.3 unfiled | product | `tests/surface/` `test-oplog_rotation` | `tools/provenance.tsv` | none | - | - | filed by W20 |
| W48 | 3 | W48-G3-S2 | U-078.4 unfiled | product | none | none | none | - | - | filed by W45 |
| W48 | filing | W48-F01 | U-047 unfiled | product | none | `ROADMAP.md`, `docs/item_notes/phase5.md`, `docs/LEDGER.md` | none | - | - | - |
| W49 | 1 | W49-G1-S1 | CS-1431 part 1 | product | `clockspeed/advisor/rules/` `progress`, `tests/advisor/rules/` `test-progress` | `docs/LEDGER.md`, `tools/provenance.tsv` | none | - | - | - |
| W49 | 1 | W49-G1-S2 | CS-1427 part 2 | product | `clockspeed/advisor/rules/` `transport`, `tests/advisor/rules/` `test-transport` | `tools/provenance.tsv` | none | - | - | - |
| W49 | 2 | W49-G2-S1 | CS-1433 part 2 | product | none | none | none | - | - | - |
| W49 | 2 | W49-G2-S2 | U-047 unfiled | product | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase5.md` | none | - | - | filed by W48 |
| W49 | 3 | W49-G3-S1 | CS-458.1 | process | none | none | none | - | - | - |
| W49 | filing | W49-F01 | U-066 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W50 | 1 | W50-G1-S1 | CS-1433 part 3 | product | none | none | none | - | - | - |
| W50 | 1 | W50-G1-S2 | U-066 unfiled | product | none | `BACKLOG.md` | none | - | - | filed by W49 |
| W50 | 2 | W50-G2-S1 | CS-1058.5 | product | none | none | none | - | - | extension filed by W3; child row filed by W3 |
| W50 | 2 | W50-G2-S2 | U-125.9 unfiled | product | none | `tools/provenance.tsv` | none | - | - | filed by W20 |
| W50 | 3 | W50-G3-S1 | CS-1433 part 4 | product | none | `ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md` | none | - | - | - |
| W50 | 3 | W50-G3-S2 | CS-807.1 | process | none | none | none | - | - | - |
| W50 | filing | W50-F01 | U-055 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W50 | filing | W50-F02 | U-067 unfiled | product | none | `ROADMAP.md`, `docs/item_notes/phase5.md`, `docs/LEDGER.md` | none | - | - | - |
| W50 | lane | W50-L01 | CS-1071 | process | none | none | none | lane gap | - | - |
| W51 | 1 | W51-G1-S1 | U-055.1 unfiled | product | `tests/advisor/` `test-world_defaults` | `tools/provenance.tsv` | none | - | - | filed by W50 |
| W51 | 1 | W51-G1-S2 | U-125.4 unfiled | product | none | none | none | - | - | filed by W20 |
| W51 | 2 | W51-G2-S1 | U-022.2 unfiled | product | none | none | none | - | - | filed by W47 |
| W51 | 2 | W51-G2-S2 | CS-1431 part 2 | product | none | none | none | - | - | - |
| W51 | 3 | W51-G3-S1 | U-125.5 unfiled | product | none | none | none | - | - | filed by W20 |
| W51 | 3 | W51-G3-S2 | U-067 unfiled | product | none | none | none | - | - | filed by W50 |
| W51 | filing | W51-F01 | U-069 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W52 | 1 | W52-G1-S1 | CS-1427 part 3 | product | none | none | none | - | - | - |
| W52 | 1 | W52-G1-S2 | CS-916.2 | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/GATED.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | - |
| W52 | 2 | W52-G2-S1 | U-022.3 unfiled | product | none | none | none | - | - | filed by W47 |
| W52 | 2 | W52-G2-S2 | U-069 unfiled | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | none | - | - | filed by W51 |
| W52 | filing | W52-F01 | U-070 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W53 | 1 | W53-G1-S1 | U-125.6 unfiled | product | none | none | none | - | - | filed by W20 |
| W53 | 1 | W53-G1-S2 | U-070 unfiled | product | none | none | none | - | - | filed by W52 |
| W53 | 2 | W53-G2-S1 | U-125.7 unfiled | product | `shell/lib/` `oplog`, `shell/test/` `oplog.test`, `tests/shell/` `test-oplog_binding` | `tools/provenance.tsv` | none | - | - | filed by W20 |
| W53 | 2 | W53-G2-S2 | CS-1058.6 | product | none | none | none | - | - | extension filed by W3; child row filed by W3 |
| W53 | 3 | W53-G3-S1 | U-055.2 unfiled | product | none | none | none | - | - | filed by W50 |
| W53 | 3 | W53-G3-S2 | CS-1431 part 3 | product | none | `docs/ARCHITECTURE.md` | none | - | - | - |
| W53 | filing | W53-F01 | U-124 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W53 | lane | W53-L01 | CS-1074 | process | none | none | none | lane gap | - | - |
| W54 | 1 | W54-G1-S1 | U-125.10 unfiled | product | none | `tools/provenance.tsv` | none | - | - | filed by W20 |
| W54 | 1 | W54-G1-S2 | U-124.1 unfiled | product | `tests/advisor/` `test-store_recovery` | `tools/provenance.tsv` | none | - | - | filed by W53 |
| W54 | 2 | W54-G2-S1 | U-125.8 unfiled | product | none | `BACKLOG.md`, `ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | `docs/OPERATIONS.md` | - | - | filed by W20 |
| W54 | 2 | W54-G2-S2 | U-124.2 unfiled | product | none | none | none | - | - | filed by W53 |
| W54 | 3 | W54-G3-S1 | U-124.3 unfiled | product | none | `docs/ARCHITECTURE.md` | none | - | - | filed by W53 |
| W54 | filing | W54-F01 | U-092 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W54 | filing | W54-F02 | U-154 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W55 | 1 | W55-G1-S1 | CS-1262.1 | product | `clockspeed/surface/` `diagnostics`, `tests/surface/` `test-diagnostics` | `docs/item_notes/phase6.md`, `tools/provenance.tsv` | none | - | - | - |
| W55 | 1 | W55-G1-S2 | U-064.2 unfiled | product | none | none | `docs/OPERATIONS.md` | - | - | filed by W38 |
| W55 | 2 | W55-G2-S1 | CS-1262.2 | product | `tests/surface/` `test-diagnostics_redaction` | `tools/provenance.tsv` | none | - | - | - |
| W55 | 2 | W55-G2-S2 | U-154.1 unfiled | product | `docs/adr/` `NNNN-the-oodle-data-licence-verdict` | `THIRD_PARTY.md`, `docs/LEDGER.md`, `docs/adr/README.md`, `tools/provenance.tsv` | none | - | - | filed by W54 |
| W55 | 3 | W55-G3-S1 | CS-1262.3 | product | `shell/lib/` `diagnostics`, `shell/test/` `diagnostics.test` | `tools/provenance.tsv` | none | - | - | - |
| W55 | 3 | W55-G3-S2 | U-092 unfiled | product | `tests/surface/` `test-response_headers` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md`, `tools/provenance.tsv` | none | - | - | filed by W54 |
| W55 | filing | W55-F01 | U-090 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W55 | filing | W55-F02 | U-093 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W55 | filing | W55-F03 | U-121 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W56 | 1 | W56-G1-S1 | U-121.1 unfiled | product | none | `ROADMAP.md`, `docs/item_notes/phase6.md` | none | - | - | filed by W55 |
| W56 | 1 | W56-G1-S2 | U-154.2 unfiled | product | none | `docs/GATED.md`, `docs/LEDGER.md` | none | - | - | filed by W54 |
| W56 | 2 | W56-G2-S1 | CS-1262.4 | product | none | none | none | - | - | - |
| W56 | 2 | W56-G2-S2 | U-090 unfiled | product | `tests/surface/` `test-connection_discipline` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md`, `tools/provenance.tsv` | none | - | - | filed by W55 |
| W56 | 3 | W56-G3-S1 | CS-1262.5 | product | none | none | none | - | - | - |
| W56 | 3 | W56-G3-S2 | U-093 unfiled | product | `tests/surface/` `test-internal_error` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | filed by W55 |
| W56 | filing | W56-F01 | U-120 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W56 | filing | W56-F02 | U-122 unfiled | product | none | `ROADMAP.md`, `config/lane_scopes.json`, `docs/item_notes/phase6.md`, `docs/LEDGER.md` | none | - | - | - |
| W56 | lane | W56-L01 | CS-460 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | lane gap | - | - |
| W57 | 1 | W57-G1-S1 | U-122 unfiled | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | none | - | - | filed by W56 |
| W57 | 1 | W57-G1-S2 | U-120 unfiled | product | none | none | none | - | - | filed by W56 |
| W57 | 2 | W57-G2-S1 | U-121.2 unfiled | product | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | none | - | - | filed by W55 |
| W57 | 2 | W57-G2-S2 | CS-1262.6 | product | none | `ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/item_notes/phase6.md` | `docs/OPERATIONS.md` | - | - | - |
| W57 | 3 | W57-G3-S1 | CS-452.1 | product | none | none | none | - | - | - |
| W57 | 3 | W57-G3-S2 | CS-829.1 | product | none | none | none | - | - | - |
| W58 | 1 | W58-G1-S1 | CS-452.2 | product | none | none | none | - | - | - |
| W58 | 1 | W58-G1-S2 | CS-1150.1 | product | none | none | none | - | - | - |
| W58 | 2 | W58-G2-S1 | CS-1241.1 | product | none | none | none | - | - | - |
| W58 | 2 | W58-G2-S2 | CS-452.3 | product | none | `ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | - | - | - |
| W58 | 3 | W58-G3-S1 | CS-984.1 | product | `tests/save/` `test-struct_interior_seam` | none | none | - | - | - |
| W58 | 3 | W58-G3-S2 | CS-1089 | process | `tests/save/` `test-struct_interior_BLOCK` | `tools/provenance.tsv` | none | - | - | - |
| W59 | 1 | W59-G1-S1 | CS-832 | product | none | none | none | - | - | - |
| W59 | 1 | W59-G1-S2 | CS-443.1 | product | none | none | none | - | - | - |
| W59 | 2 | W59-G2-S1 | CS-829.2 | product | none | none | none | - | - | - |
| W59 | 2 | W59-G2-S2 | CS-1241.2 | product | `clockspeed/data/` `DECISIONS-TABLE`, `tests/data/` `test-build_variants`, `tests/data/` `test-decisions_table` | `config/lane_scopes.json` | none | - | - | - |
| W59 | 3 | W59-G3-S1 | CS-1150.2 | product | `tests/save/` `test-residual_redaction` | `tools/provenance.tsv` | none | - | - | - |
| W59 | 3 | W59-G3-S2 | CS-1091 | process | `tests/save/` `test-world_BLOCK` | `tools/provenance.tsv` | none | - | - | - |
| W59 | lane | W59-L01 | CS-1241.3 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase5.md`, `tools/provenance.tsv` | none | lane gap | - | - |
| W60 | 1 | W60-G1-S1 | CS-965.1 | product | none | none | none | - | - | - |
| W60 | 1 | W60-G1-S2 | CS-984.2 | product | none | `docs/ARCHITECTURE.md`, `tools/provenance.tsv` | none | - | - | - |
| W60 | 2 | W60-G2-S1 | CS-829.3 | product | none | none | none | - | - | - |
| W60 | 2 | W60-G2-S2 | CS-843.2 | product | none | none | none | - | - | - |
| W60 | 3 | W60-G3-S1 | CS-982 | product | `tests/save/` `test-tag_flag_evidence` | `tools/provenance.tsv` | none | - | - | - |
| W60 | 3 | W60-G3-S2 | CS-443.2 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4.md` | none | - | - | - |
| W60 | lane | W60-L01 | CS-446 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4.md` | none | lane gap | - | - |
| W61 | 1 | W61-G1-S1 | CS-965.2 | product | none | none | none | - | - | - |
| W61 | 1 | W61-G1-S2 | CS-462 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | - | - | - |
| W61 | 2 | W61-G2-S1 | CS-1053.1 | product | `tests/save/` `test-adr_0016_agreement` | none | none | - | - | - |
| W61 | 2 | W61-G2-S2 | CS-986 | product | `tests/save/` `test-native_struct_population` | `tools/provenance.tsv` | none | - | - | - |
| W61 | 3 | W61-G3-S1 | CS-828 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4-followups.md` | none | - | - | - |
| W61 | 3 | W61-G3-S2 | CS-1053.2 | product | none | `docs/LEDGER.md`, `docs/adr/README.md`, `tools/provenance.tsv` | none | - | - | - |
| W62 | 1 | W62-G1-S1 | CS-861 | product | none | none | none | - | - | - |
| W62 | 1 | W62-G1-S2 | CS-440.3 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4.md` | none | - | - | - |
| W62 | 2 | W62-G2-S1 | CS-449.1 | product | none | none | none | - | - | - |
| W62 | 2 | W62-G2-S2 | CS-829.4 | product | none | none | none | - | - | - |
| W62 | 3 | W62-G3-S1 | CS-965.3 | product | `docs/adr/` `NNNN-cs-965-SLUG` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/adr/README.md`, `docs/item_notes/phase4-followups-960.md`, `tools/provenance.tsv` | none | - | - | - |
| W62 | 3 | W62-G3-S2 | CS-852.1 | process | none | none | none | - | - | - |
| W63 | 1 | W63-G1-S1 | CS-843.3 | product | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups.md` | none | - | - | - |
| W63 | 1 | W63-G1-S2 | CS-1090 | process | `tests/save/` `test-properties_BLOCK` | `tools/provenance.tsv` | none | - | - | - |
| W63 | 2 | W63-G2-S1 | CS-1052 | product | none | none | none | - | - | - |
| W63 | 2 | W63-G2-S2 | CS-988.1 | process | none | none | none | - | - | - |
| W63 | 3 | W63-G3-S1 | CS-988.2 | process | none | none | none | - | - | - |
| W63 | 3 | W63-G3-S2 | CS-860.1 | process | none | none | none | - | - | - |
| W63 | lane | W63-L01 | CS-1004 | process | none | none | none | lane gap | - | - |
| W64 | 1 | W64-G1-S1 | CS-1056.1 | process | `tests/save/` `test-oracle_pair_coverage` | none | none | - | - | - |
| W64 | 1 | W64-G1-S2 | CS-988.3 | process | none | none | none | - | - | - |
| W64 | 2 | W64-G2-S1 | CS-458.2 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | - | - | - |
| W64 | 2 | W64-G2-S2 | CS-988.4 | process | none | none | none | - | - | - |
| W64 | 3 | W64-G3-S1 | CS-412.1 | process | none | none | none | - | - | - |
| W64 | 3 | W64-G3-S2 | CS-1358.1 | process | `tests/` `tree_population`, `tests/` `test-tree_population` | none | none | - | - | - |
| W65 | 1 | W65-G1-S1 | CS-455 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | - | - | - |
| W65 | 1 | W65-G1-S2 | CS-1358.2 | process | none | none | none | - | - | - |
| W65 | 2 | W65-G2-S1 | CS-943 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4-followups-900.md` | none | - | - | - |
| W65 | 2 | W65-G2-S2 | CS-1092 | process | none | none | none | - | - | - |
| W65 | 3 | W65-G3-S1 | CS-860.2 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | - | - | - |
| W65 | 3 | W65-G3-S2 | CS-1131 | process | `tests/data/` `test-drift_guard_work_items_orphans` | `tools/provenance.tsv` | none | - | - | - |
| W66 | 1 | W66-G1-S1 | CS-1010.1 | process | none | none | none | - | - | - |
| W66 | 1 | W66-G1-S2 | CS-1077 | process | none | none | none | - | - | - |
| W66 | 2 | W66-G2-S1 | CS-988.5 | process | none | none | none | - | - | - |
| W66 | 2 | W66-G2-S2 | CS-852.2 | process | none | none | none | - | - | - |
| W66 | 3 | W66-G3-S1 | CS-945.1 | process | `tools/` `branch_census`, `tests/` `test-branch_census` | none | none | - | - | - |
| W66 | 3 | W66-G3-S2 | CS-1010.2 | process | none | none | none | - | - | - |
| W66 | lane | W66-L01 | CS-1010.3 | process | none | `docs/item_notes/phase4-followups-1000.md` | none | lane gap | - | - |
| W67 | 1 | W67-G1-S1 | CS-855.1 | process | none | none | none | - | - | - |
| W67 | 1 | W67-G1-S2 | CS-988.6 | process | none | none | none | - | - | - |
| W67 | 2 | W67-G2-S1 | CS-910.1 | process | none | `config/lane_scopes.json` | none | - | - | - |
| W67 | 2 | W67-G2-S2 | CS-1149.1 | process | none | none | none | - | - | - |
| W67 | 3 | W67-G3-S1 | CS-859 | process | none | none | none | - | - | - |
| W67 | 3 | W67-G3-S2 | CS-1358.3 | process | none | none | none | - | - | - |
| W68 | 1 | W68-G1-S1 | CS-1094 | process | none | none | none | - | - | - |
| W68 | 1 | W68-G1-S2 | CS-1078 | process | none | none | none | - | - | - |
| W68 | 2 | W68-G2-S1 | CS-499.1 | process | none | none | none | - | - | - |
| W68 | 2 | W68-G2-S2 | CS-1055.1 | process | `tests/` `write_tracer` | none | none | - | - | - |
| W68 | 3 | W68-G3-S1 | CS-910.2 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase6.md` | none | - | - | - |
| W68 | 3 | W68-G3-S2 | CS-1063 | process | none | `docs/item_notes/phase4-followups-1000.md` | none | - | - | - |
| W69 | 1 | W69-G1-S1 | CS-1130.2 | process | `tools/` `ACCEPTANCE-CLAUSE-PIN-RECORD` | `docs/LEDGER.md`, `tools/provenance.tsv` | none | - | - | - |
| W69 | 1 | W69-G1-S2 | CS-1149.2 | process | `tests/save/` `test-residual_census` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4-followups-1000.md`, `docs/item_notes/phase4-followups.md`, `tools/provenance.tsv` | none | - | - | - |
| W69 | 2 | W69-G2-S1 | CS-1075.1 | process | none | none | none | - | - | - |
| W69 | 2 | W69-G2-S2 | CS-1295.1 | process | `docs/_archive/` `DATE-cs1295-repo-review-plan-2`, `docs/_archive/` `DATE-cs1295-repo-review-findings-2` | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase7.md`, `tools/provenance.tsv` | none | - | - | - |
| W69 | 3 | W69-G3-S1 | CS-439.1 | process | none | none | none | - | - | - |
| W69 | 3 | W69-G3-S2 | CS-946 | process | `docs/adr/` `NNNN-cs-946-SLUG` | `ROADMAP.md`, `docs/LEDGER.md`, `docs/adr/README.md`, `docs/item_notes/phase4-followups-900.md`, `tools/provenance.tsv` | none | - | - | - |
| W70 | 1 | W70-G1-S1 | CS-1129 | process | none | none | none | - | - | - |
| W70 | 1 | W70-G1-S2 | CS-807.2 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups.md` | none | - | - | - |
| W70 | 2 | W70-G2-S1 | CS-499.2 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4.md` | none | - | - | - |
| W70 | 2 | W70-G2-S2 | CS-966 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/item_notes/phase4-followups-960.md` | none | - | - | - |
| W70 | 3 | W70-G3-S1 | CS-1055.2 | process | `tests/` `test-live_copies_guard`, `tests/` `test-write_tracer` | `tools/provenance.tsv` | `docs/OPERATIONS.md` | - | - | - |
| W70 | 3 | W70-G3-S2 | CS-439.2 | process | `tests/` `test-silent_loss_guard` | none | none | - | - | - |
| W70 | lane | W70-L01 | CS-1141 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-1000.md` | none | lane gap | - | - |
| W71 | 1 | W71-G1-S1 | CS-988.7 | process | none | none | none | - | - | - |
| W71 | 1 | W71-G1-S2 | CS-1056.2 | process | none | `tools/provenance.tsv` | none | - | - | - |
| W71 | 2 | W71-G2-S1 | CS-1137 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-1000.md` | none | - | - | - |
| W71 | 2 | W71-G2-S2 | CS-945.2 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `tools/provenance.tsv` | none | - | - | - |
| W71 | 3 | W71-G3-S1 | CS-472.1 | process | none | none | none | - | - | - |
| W71 | 3 | W71-G3-S2 | CS-1075.2 | process | none | none | none | - | - | - |
| W72 | 1 | W72-G1-S1 | CS-604 | process | none | `BACKLOG.md` | `BOOTSTRAP.md`, `docs/OPERATIONS.md` | - | - | - |
| W72 | 1 | W72-G1-S2 | CS-1358.4 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase7.md`, `tools/provenance.tsv` | none | - | - | - |
| W72 | 2 | W72-G2-S1 | CS-610 | process | none | none | none | - | - | - |
| W72 | 2 | W72-G2-S2 | CS-1295.2 | process | none | `BACKLOG.md`, `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase7.md`, `tools/provenance.tsv` | none | - | - | - |
| W72 | 3 | W72-G3-S1 | CS-477.1 | process | none | none | none | - | - | - |
| W72 | 3 | W72-G3-S2 | CS-615 | process | `shell/` `suite_counts` | `tools/provenance.tsv` | none | - | - | - |
| W73 | 1 | W73-G1-S1 | CS-606 | process | `tests/surface/` `test-entry_serve` | `docs/item_notes/phase6.md`, `tools/provenance.tsv` | none | - | - | - |
| W73 | 1 | W73-G1-S2 | CS-855.2 | process | none | none | none | - | - | - |
| W73 | lane | W73-L01 | CS-1135 | process | none | `ROADMAP.md`, `docs/LEDGER.md`, `docs/history_notes.md`, `docs/item_notes/phase4-followups-1000.md` | none | lane gap | - | - |
