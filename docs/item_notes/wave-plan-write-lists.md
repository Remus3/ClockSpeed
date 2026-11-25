# Clockspeed - the wave table's Write-list column, an annex

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**This file is an ANNEX to `docs/item_notes.md`, not a phase leaf.** It carries no item
section and no `## CS-nnn` heading, so `tools/drift_guard.py` guard (j) neither routes to
it nor reads a section out of it. It holds the Write-list column of the wave table in
`docs/item_notes/wave-plan.md`, one row per slice keyed by the Slice cell, in that table's
row order; every other column stays in the wave table.

## Write-list table

| Slice | Write-list |
|---|---|
| W0a-M01 | none |
| W0a-M02 | `tests/test_citation_tables.py` |
| W0a-M03 | none |
| W0a-M04 | none |
| W0a-M05 | none |
| W0a-M06 | none |
| W0a-M07 | none |
| W0a-M08 | none |
| W0b-M01 | none |
| W0b-M02 | none |
| W0b-M03 | `docs/item_notes.md` |
| W0b-M04 | none |
| W0b-M05 | none |
| W0b-M06 | none |
| W0b-M07 | none |
| W0b-M08 | none |
| W0b-M09 | none |
| W0b-M10 | none |
| W0b-M11 | none |
| W0b-M12 | none |
| W0b-M13 | none |
| W0b-M14 | `tests/ops/test_lane_scope.py` |
| W0b-M15 | none |
| W0b-M16 | none |
| W0-G1-S1 | `clockspeed/save/world.py`, `tests/save/test_world.py` |
| W0-G1-S2 | `tests/test_pretooluse_gate.py`, `tests/save/test_synthetic.py`, `tests/save/test_phase4_gate.py`, `tests/surface/test_server.py`, `tests/test_hook_interpreter_ladder.py`, `tests/surface/test_map.py`, `tests/test_fleet_kit.py`, `tests/ops/test_suite_ration.py`, `ops/loop/queue_loop.py`, `clockspeed/save/objects.py`, `tests/save/test_zero_remainder.py`, `tests/surface/test_panel_solve.py`, `tests/surface/test_panel_power.py`, `tests/surface/test_panel_optimize.py`, `tests/surface/test_solve.py`, `tests/surface/panel_harness.py`, `tests/surface/test_web_assets.py`, `tests/test_claude_hook.py` |
| W0-G2-S1 | `clockspeed/save/workdir.py`, `clockspeed/data/version.py`, `tests/save/test_workdir.py`, `tests/data/test_version.py` |
| W0-G2-S2 | `clockspeed/solve/exact.py`, `tests/solve/test_exact.py` |
| W1-G1-S1 | `clockspeed/surface/web/app.js` |
| W1-G1-S2 | `clockspeed/advisor/advise.py`, `clockspeed/advisor/ranking.py`, `tests/advisor/test_interleave.py`, `tests/advisor/test_advise.py`, `tests/test_citation_tables.py`, `tests/test_pointer_claims.py`, `tests/advisor/test_ranking.py` |
| W1-G2-S1 | `clockspeed/surface/web/index.html`, `clockspeed/surface/server.py`, `tests/surface/test_server.py`, `clockspeed/surface/web/app.js`, `tests/surface/test_web_assets.py`, `tests/surface/` `test-panel_diagnostics` |
| W1-G2-S2 | `clockspeed/data/locate.py`, `tests/data/test_locate.py`, `tests/save/test_workdir.py` |
| W1-G3-S1 | `scripts/make_cert.py`, `tests/test_make_cert.py`, `clockspeed/surface/server.py`, `clockspeed/surface/api/contract.py`, `tests/surface/test_server.py`, `tests/surface/test_contract.py` |
| W1-G3-S2 | `README.md` |
| W1-L01 | `clockspeed/surface/__main__.py`, `clockspeed/surface/server.py`, `tests/surface/test_server.py`, `tests/ops/test_lane_scope.py` |
| W2-G1-S1 | `tools/dashboard_probe.py`, `tests/test_dashboard_probe.py` |
| W2-G1-S2 | none |
| W2-G2-S1 | `clockspeed/surface/api/health.py`, `clockspeed/surface/providers.py`, `clockspeed/surface/api/contract.py`, `tests/surface/test_health.py`, `clockspeed/surface/web/app.js`, `clockspeed/surface/api/routes.py` |
| W2-G2-S2 | `tests/test_redaction_scope.py`, `tests/save/reach_guard.py` |
| W2-G3-S1 | `tests/ops/test_lane_scope.py` |
| W2-G3-S2 | none |
| W2-F01 | none |
| W3-G1-S1 | `shell/main.js`, `tests/shell/test_shell_assets.py` |
| W3-G1-S2 | `shell/package.json`, `shell/package-lock.json`, `tests/shell/test_shell_dependency_floor.py` |
| W3-G2-S1 | `clockspeed/surface/server.py`, `tests/surface/test_server.py`, `clockspeed/surface/api/health.py` |
| W3-G2-S2 | `clockspeed/data/locate.py`, `tests/data/test_locate.py`, `clockspeed/advisor/ledger.py`, `tests/advisor/test_ledger.py`, `clockspeed/save/workdir.py`, `tests/save/test_workdir.py`, `tests/conftest.py` |
| W3-G3-S1 | `clockspeed/surface/web/app.css` |
| W3-G3-S2 | none |
| W3-F01 | none |
| W3-F02 | none |
| W3-L01 | `shell/lib/state.js`, `shell/test/state.test.js`, `tests/ops/test_lane_scope.py` |
| W4-G1-S1 | `clockspeed/surface/api/contract.py`, `tests/surface/test_contract.py`, `clockspeed/surface/server.py`, `tests/surface/` `test-admission` |
| W4-G1-S2 | `clockspeed/surface/web/index.html`, `clockspeed/surface/web/app.js`, `clockspeed/surface/web/app.css`, `tests/surface/test_web_assets.py`, `tests/surface/test_panel_seam.py`, `tests/surface/panel_harness.py`, `tests/surface/test_panel_global_scope.py` |
| W4-G2-S1 | `clockspeed/surface/api/routes.py`, `tests/surface/` `test-admission`, `clockspeed/surface/server.py` |
| W4-G2-S2 | `clockspeed/surface/config.py`, `tests/surface/test_config.py`, `clockspeed/data/assets.py`, `tests/data/test_assets.py`, `clockspeed/surface/__main__.py`, `tests/surface/test_routes.py`, `tests/data/` `test-data_root` |
| W4-G3-S1 | `clockspeed/advisor/ledger.py`, `clockspeed/advisor/` `annotations`, `tests/advisor/` `test-annotations`, `tests/advisor/test_ledger.py` |
| W4-G3-S2 | `clockspeed/save/world.py`, `tests/save/test_world.py` |
| W4-F01 | none |
| W5-G1-S1 | `clockspeed/surface/web/app.css`, `tools/dashboard_probe.py`, `tests/test_dashboard_probe.py`, `clockspeed/surface/web/app.js`, `tests/surface/` `test-views`, `tests/surface/test_web_assets.py`, `tests/surface/panel_harness.py`, `tests/surface/test_panel_global_scope.py` |
| W5-G1-S2 | `shell/lib/endpoint.js`, `shell/test/endpoint.test.js`, `tests/data/` `test-data_root` |
| W5-G2-S1 | none |
| W5-G2-S2 | `tests/surface/audit_harness.py`, `tests/surface/test_web_assets.py` |
| W5-G3-S1 | `clockspeed/save/world.py`, `tests/save/test_world.py` |
| W5-G3-S2 | `clockspeed/data/registry.py`, `tests/data/test_transport_rates.py` |
| W5-F01 | none |
| W5-F02 | none |
| W5-F03 | none |
| W6-G1-S1 | `shell/lib/window.js`, `shell/test/window.test.js`, `shell/main.js`, `tests/shell/test_shell_assets.py`, `shell/lib/endpoint.js`, `shell/test/endpoint.test.js` |
| W6-G1-S2 | `clockspeed/surface/web/index.html`, `clockspeed/surface/server.py`, `tests/surface/test_server.py`, `tests/surface/test_web_assets.py`, `clockspeed/surface/web/app.js` |
| W6-G2-S1 | `docs/adr/0015-the-shell-may-start-the-surface.md` |
| W6-G2-S2 | `clockspeed/surface/web/` `panel_play`, `tests/surface/` `test-panel_play`, `clockspeed/surface/web/index.html`, `clockspeed/surface/server.py`, `tests/surface/test_server.py`, `tests/surface/test_web_assets.py`, `clockspeed/surface/web/app.js` |
| W6-G3-S1 | `shell/lib/tray.js`, `shell/test/tray.test.js`, `shell/main.js` |
| W6-G3-S2 | `tools/measurements.json` |
| W6-F01 | none |
| W6-L01 | `tests/solve/test_ratio.py`, `tests/solve/synthetic.py` |
| W7-G1-S1 | `clockspeed/surface/web/app.css`, `tests/surface/` `test-panel_play`, `clockspeed/surface/web/` `panel_play`, `tests/surface/test_web_assets.py` |
| W7-G1-S2 | `shell/lib/tray.js`, `shell/test/tray.test.js` |
| W7-G2-S1 | `clockspeed/surface/web/app.css`, `tests/surface/test_web_assets.py` |
| W7-G2-S2 | `clockspeed/audit/__init__.py`, `clockspeed/advisor/advise.py`, `tests/advisor/test_advise.py`, `clockspeed/advisor/cards.py`, `tests/advisor/test_cards.py`, `clockspeed/surface/providers.py`, `clockspeed/surface/api/provenance.py`, `clockspeed/surface/api/contract.py`, `tests/surface/test_contract.py` |
| W7-G3-S1 | `tests/surface/test_web_assets.py`, `tests/surface/test_panel_global_scope.py` |
| W7-G3-S2 | `shell/test/window.test.js`, `tests/shell/test_shell_assets.py`, `shell/test/supervisor.test.js`, `shell/test/tray.test.js`, `shell/test/verdict.test.js` |
| W7-F01 | none |
| W7-F02 | none |
| W7-F03 | none |
| W8-G1-S1 | `clockspeed/surface/providers.py`, `tests/surface/test_schematic_source.py`, `clockspeed/surface/__main__.py`, `tools/measurements.json` |
| W8-G1-S2 | `tests/surface/test_web_assets.py`, `clockspeed/surface/web/app.css`, `tests/surface/test_panel_advice.py`, `tests/surface/test_panel_advice_layout.py` |
| W8-G2-S1 | `clockspeed/surface/__main__.py`, `tests/surface/test_routes.py`, `tests/surface/test_schematic_source.py` |
| W8-G2-S2 | `shell/main.js`, `tests/shell/test_shell_assets.py` |
| W8-G3-S1 | `tests/shell/test_shell_dependency_floor.py` |
| W8-G3-S2 | `scripts/make_shortcut.py`, `tests/test_make_shortcut.py`, `tests/conftest.py` |
| W8-F01 | none |
| W8-F02 | none |
| W9-G1-S1 | `clockspeed/surface/api/advice.py`, `tests/surface/test_advice.py`, `clockspeed/surface/api/world.py`, `tests/surface/test_world.py`, `clockspeed/surface/api/map.py`, `tests/surface/test_map.py`, `clockspeed/surface/api/power.py`, `tests/surface/test_power.py`, `clockspeed/surface/api/solve.py`, `tests/surface/test_solve.py`, `clockspeed/surface/api/health.py`, `tests/surface/test_health.py` |
| W9-G1-S2 | `clockspeed/surface/web/app.js`, `tests/surface/test_panel_seam.py`, `tests/surface/test_web_assets.py`, `tests/surface/test_panel_solve.py` |
| W9-G2-S1 | `clockspeed/surface/providers.py`, `clockspeed/surface/` `priority`, `tests/surface/` `test-priority` |
| W9-G2-S2 | `tests/shell/test_shell_assets.py` |
| W9-G3-S1 | `tests/shell/test_shell_assets.py` |
| W9-G3-S2 | `tools/drift_guard.py` |
| W9-F01 | none |
| W10-G1-S1 | `clockspeed/save/workdir.py`, `tests/save/test_workdir.py` |
| W10-G1-S2 | `clockspeed/surface/api/registry.py`, `tests/surface/test_registry.py`, `clockspeed/surface/web/app.js`, `clockspeed/surface/web/panel_advice.js`, `tests/surface/test_panel_advice.py`, `clockspeed/surface/web/app.css`, `clockspeed/surface/web/index.html`, `shell/lib/tray.js`, `shell/test/tray.test.js` |
| W10-G2-S1 | `tests/surface/` `test-panel_repaint`, `tests/surface/test_panel_solve.py`, `clockspeed/surface/web/app.js` |
| W10-G2-S2 | `tests/surface/test_world_provider_memo.py`, `clockspeed/surface/providers.py`, `clockspeed/surface/api/health.py`, `clockspeed/surface/api/routes.py`, `clockspeed/surface/__main__.py`, `tests/surface/test_health.py` |
| W10-G3-S1 | `.github/workflows/tier2.yml`, `tests/shell/test_shell_assets.py` |
| W10-G3-S2 | `clockspeed/save/objects.py`, `tests/save/test_reference_resolution.py` |
| W11-G1-S1 | `shell/main.js`, `tests/shell/test_shell_assets.py` |
| W11-G1-S2 | `tests/save/test_newest_world.py`, `tests/surface/test_world_provider_fallback.py`, `tests/surface/test_world_provider_memo.py`, `clockspeed/surface/providers.py`, `clockspeed/save/world.py`, `tests/ops/test_lane_scope.py` |
| W11-G2-S1 | `tests/audit/test_package_exports.py`, `tests/surface/test_advice_act.py`, `tests/surface/test_advice_golden.py`, `tests/surface/golden/advice_no_target.json`, `tests/surface/test_advice_source.py`, `tests/surface/test_registry_state_served.py`, `tests/surface/test_web_assets.py`, `tests/surface/panel_harness.py`, `tests/surface/audit_harness.py` |
| W11-G2-S2 | `clockspeed/surface/web/app.js`, `clockspeed/surface/web/` `panel_play`, `tests/surface/test_panel_seam.py`, `tests/surface/` `test-panel_play`, `tests/surface/` `test-panel_repaint` |
| W11-G3-S1 | `docs/adr/0014-the-shell-trusts-one-pinned-certificate.md` |
| W11-G3-S2 | `tests/test_mypy_gate.py` |
| W11-F01 | none |
| W11-F02 | none |
| W11-F03 | none |
| W12-G1-S1 | `tests/surface/test_world_provider_memo.py`, `tests/surface/` `test-health_readiness`, `clockspeed/surface/providers.py`, `clockspeed/surface/api/health.py`, `clockspeed/surface/api/routes.py`, `clockspeed/surface/__main__.py`, `tests/surface/test_health.py` |
| W12-G1-S2 | `shell/main.js`, `tests/shell/test_shell_assets.py`, `scripts/make_shortcut.py`, `tests/test_make_shortcut.py` |
| W12-G2-S1 | `tools/measurements.json` |
| W12-G2-S2 | `shell/lib/window.js`, `shell/test/window.test.js` |
| W12-G3-S1 | `shell/lib/` `guard`, `shell/test/` `guard.test` |
| W12-G3-S2 | `clockspeed/surface/__main__.py`, `tests/surface/test_server.py`, `tests/surface/test_routes.py` |
| W12-F01 | none |
| W12-F02 | none |
| W13-G1-S1 | none |
| W13-G1-S2 | `clockspeed/save/workdir.py`, `tests/save/test_workdir.py`, `clockspeed/surface/__main__.py`, `clockspeed/save/world.py`, `tests/save/test_newest_world.py`, `tests/save/test_world.py`, `tests/save/test_phase4_gate.py` |
| W13-G2-S1 | `clockspeed/surface/server.py`, `tests/surface/test_server.py` |
| W13-G2-S2 | none |
| W13-G3-S1 | `clockspeed/surface/__main__.py`, `tests/surface/` `test-watch` |
| W13-G3-S2 | `tests/test_citation_tables.py` |
| W13-F01 | none |
| W13-F02 | none |
| W13-F03 | none |
| W13-L01 | `tests/test_scaffold.py` |
| W14-G1-S1 | `shell/main.js`, `tests/shell/test_shell_assets.py` |
| W14-G1-S2 | `pyproject.toml` |
| W14-G2-S1 | `scripts/make_cert.py`, `tests/test_make_cert.py`, `tests/toolpath_guard.py`, `tests/test_toolpath.py` |
| W14-G2-S2 | `shell/lib/window.js`, `shell/test/window.test.js`, `shell/main.js`, `tests/shell/test_shell_assets.py` |
| W14-G3-S1 | `shell/lib/window.js`, `shell/test/window.test.js`, `shell/main.js`, `tests/shell/test_shell_assets.py` |
| W14-G3-S2 | `clockspeed/surface/web/app.css`, `tests/surface/test_web_assets.py` |
| W15-G1-S1 | `clockspeed/surface/web/app.js`, `clockspeed/surface/web/index.html`, `clockspeed/surface/web/app.css`, `tests/surface/test_web_assets.py` |
| W15-G1-S2 | `installer/manifest`, `tools/` `release_build` |
| W15-G2-S1 | `shell/lib/supervisor.js`, `shell/test/supervisor.test.js`, `shell/main.js`, `tests/shell/test_shell_assets.py` |
| W15-G2-S2 | `tests/` `test-runtime_pins` |
| W15-G3-S1 | `shell/package.json` |
| W15-G3-S2 | `tests/surface/test_web_assets.py`, `tests/surface/test_panel_warnings.py` |
| W15-F01 | none |
| W16-G1-S1 | `shell/lib/supervisor.js`, `shell/test/supervisor.test.js`, `shell/main.js`, `shell/lib/trust.js`, `shell/test/trust.test.js`, `tests/shell/test_shell_assets.py` |
| W16-G1-S2 | `clockspeed/surface/web/app.js`, `clockspeed/surface/web/index.html`, `clockspeed/surface/web/app.css`, `clockspeed/surface/web/` `panel_play`, `clockspeed/surface/web/panel_advice.js`, `tests/surface/test_panel_advice.py`, `tests/surface/` `test-freshness_strip`, `tests/surface/` `test-panel_play`, `tests/surface/test_web_assets.py` |
| W16-G2-S1 | `tests/test_readme_audit.py`, `README.md` |
| W16-G2-S2 | `docs/adr/0013-electron-licence-gate.md`, `tests/` `test-runtime_pins`, `config/` `runtime_pins` |
| W16-G3-S1 | `installer/__init__`, `config/` `runtime_pins`, `pyproject.toml`, `installer/manifest`, `tests/` `installer/test-manifest` |
| W16-G3-S2 | `clockspeed/surface/web/index.html`, `clockspeed/surface/web/app.js`, `tools/dashboard_probe.py`, `tests/test_dashboard_probe.py`, `tests/surface/test_web_assets.py` |
| W16-F01 | none |
| W16-L01 | `tests/data/test_locate.py` |
| W17-G1-S1 | `shell/main.js`, `tests/shell/test_shell_assets.py` |
| W17-G1-S2 | `tests/surface/test_web_assets.py`, `clockspeed/surface/web/app.js` |
| W17-G2-S1 | `docs/adr/0014-the-shell-trusts-one-pinned-certificate.md` |
| W17-G2-S2 | `README.md` |
| W17-G3-S1 | none |
| W17-G3-S2 | `installer/__init__`, `installer/__main__`, `installer/cli`, `tests/` `installer/test-cli`, `config/` `runtime_pins`, `pyproject.toml`, `installer/manifest`, `tests/` `installer/test-manifest` |
| W18-G1-S1 | `shell/package.json`, `shell/package-lock.json`, `tests/shell/test_shell_dependency_floor.py` |
| W18-G1-S2 | `installer/fuses`, `tests/` `installer/test-fuses` |
| W18-G2-S1 | none |
| W18-G2-S2 | `shell/lib/supervisor.js`, `shell/test/supervisor.test.js`, `shell/main.js`, `tests/shell/test_shell_assets.py` |
| W18-G3-S1 | `tests/test_make_cert.py`, `scripts/make_cert.py` |
| W18-G3-S2 | `tests/test_facts_probe.py` |
| W19-G1-S1 | `installer/cli` |
| W19-G1-S2 | none |
| W19-G2-S1 | `installer/engine`, `tests/` `installer/test-engine`, `installer/cli` |
| W19-G2-S2 | none |
| W19-G3-S1 | `tests/save/independent_table.py`, `tests/save/test_independent_table.py`, `tests/save/synthetic.py` |
| W19-G3-S2 | `tests/save/test_oracle_citations.py`, `clockspeed/save/objects.py` |
| W19-F01 | none |
| W19-F02 | none |
| W19-F03 | none |
| W20-G1-S1 | none |
| W20-G1-S2 | `installer/selftest`, `tests/` `installer/test-selftest`, `installer/engine`, `installer/cli` |
| W20-G2-S1 | `installer/bootstrap/install`, `installer/bootstrap/install`, `installer/bootstrap/mint`, `installer/mint`, `tests/` `installer/test-mint`, `tests/` `installer/test-bootstrap_text`, `installer/selftest`, `tests/` `installer/test-selftest`, `installer/engine`, `installer/cli` |
| W20-G2-S2 | `shell/lib/supervisor.js`, `shell/test/supervisor.test.js`, `shell/lib/tray.js`, `shell/test/tray.test.js` |
| W20-G3-S1 | `tests/surface/` `test-web_palette` |
| W20-G3-S2 | none |
| W20-F01 | none |
| W20-F02 | none |
| W20-F03 | none |
| W20-L01 | `tests/save/reach_guard.py`, `tests/save/test_reach_guard.py` |
| W21-G1-S1 | `README.md`, `.github/SECURITY.md`, `tests/test_readme_audit.py` |
| W21-G1-S2 | `clockspeed/solve/ratio.py`, `tests/solve/test_ratio.py`, `clockspeed/solve/carry.py`, `tests/solve/test_carry.py` |
| W21-G2-S1 | `tests/shell/test_shell_assets.py` |
| W21-G2-S2 | `clockspeed/advisor/ranking.py`, `tests/advisor/test_ranking.py`, `clockspeed/advisor/trace.py`, `tests/advisor/test_trace.py`, `clockspeed/solve/quantity.py`, `tests/solve/test_quantity.py` |
| W21-G3-S1 | `tests/surface/test_server.py` |
| W21-G3-S2 | `clockspeed/data/blobs.py`, `clockspeed/data/docs_extract.py`, `clockspeed/data/registry.py`, `tests/surface/test_registry.py` |
| W22-G1-S1 | `shell/lib/supervisor.js`, `shell/test/supervisor.test.js`, `tests/shell/test_shell_assets.py`, `tests/` `test-version_owner` |
| W22-G1-S2 | `scripts/` `make_icon`, `tests/` `test-make_icon`, `shell/lib/` `identity`, `shell/test/` `identity.test` |
| W22-G2-S1 | `shell/main.js`, `tests/shell/test_shell_assets.py`, `installer/engine`, `tests/` `installer/test-engine` |
| W22-G2-S2 | `clockspeed/advisor/trace.py`, `clockspeed/surface/api/contract.py`, `tests/surface/test_contract.py` |
| W22-G3-S1 | `tests/shell/test_shell_assets.py`, `docs/adr/` `NNNN-the-installer` |
| W22-G3-S2 | `tests/surface/test_acceptance.py` |
| W22-F01 | none |
| W23-G1-S1 | none |
| W23-G1-S2 | `tests/shell/test_shell_assets.py`, `docs/adr/` `NNNN-the-shell-supervises-for-the-whole-session`, `shell/main.js`, `shell/lib/supervisor.js`, `shell/test/supervisor.test.js`, `tools/measurements.json` |
| W23-G2-S1 | none |
| W23-G2-S2 | `tests/surface/test_advice_source.py` |
| W23-G3-S1 | `tests/surface/test_server.py`, `clockspeed/surface/server.py` |
| W23-G3-S2 | `.github/workflows/tier1.yml`, `README.md`, `tests/test_tier1_budget.py` |
| W23-F01 | none |
| W23-L01 | `tests/data/test_phase2_gate.py` |
| W24-G1-S1 | `clockspeed/surface/api/solve.py`, `tests/surface/test_solve.py`, `clockspeed/surface/api/power.py`, `tests/surface/test_power.py` |
| W24-G1-S2 | `shell/lib/supervisor.js`, `shell/main.js`, `shell/test/supervisor.test.js`, `shell/test/tray.test.js`, `tests/shell/test_shell_assets.py` |
| W24-G2-S1 | `installer/cli`, `scripts/make_shortcut.py`, `tests/test_make_shortcut.py`, `installer/manifest`, `tests/` `installer/test-manifest`, `tests/` `installer/test-shellint`, `tests/` `installer/test-uninstall` |
| W24-G2-S2 | `clockspeed/surface/api/pending.py`, `tests/surface/test_pending.py`, `clockspeed/surface/api/routes.py`, `tests/surface/test_routes.py`, `clockspeed/surface/api/contract.py`, `tests/surface/test_contract.py`, `tests/surface/test_pending_route_count.py`, `tests/surface/test_route_table_binding.py`, `tests/surface/test_acceptance.py`, `tests/surface/audit_harness.py`, `tests/surface/test_web_assets.py`, `tests/surface/test_panel_scope.py` |
| W24-G3-S1 | `clockspeed/surface/providers.py`, `clockspeed/surface/api/` `audit`, `clockspeed/surface/api/` `plan`, `tests/surface/` `test-audit`, `tests/surface/` `test-plan` |
| W24-G3-S2 | `tests/surface/test_web_assets.py`, `tests/surface/audit_harness.py` |
| W24-F01 | none |
| W25-G1-S1 | `clockspeed/surface/api/flow_view.py`, `tests/surface/test_flow_view.py`, `clockspeed/surface/api/advice.py` |
| W25-G1-S2 | none |
| W25-G2-S1 | `clockspeed/surface/web/panel_solve.js`, `clockspeed/surface/web/panel_power.js` |
| W25-G2-S2 | `installer/cli`, `installer/engine`, `installer/update`, `tests/` `installer/test-update` |
| W25-G3-S1 | `README.md`, `tests/ops/test_lane_scope.py` |
| W25-G3-S2 | `tests/save/test_world.py` |
| W25-F01 | none |
| W25-F02 | none |
| W26-G1-S1 | `clockspeed/surface/api/power.py`, `tests/surface/test_power.py`, `clockspeed/surface/web/panel_power.js`, `tests/surface/test_panel_power.py`, `tests/surface/audit_harness.py`, `tests/ops/test_lane_scope.py` |
| W26-G1-S2 | `clockspeed/surface/web/panel_advice.js` |
| W26-G2-S1 | `tests/shell/test_shell_assets.py`, `README.md`, `shell/lib/tray.js`, `shell/test/tray.test.js`, `shell/main.js` |
| W26-G2-S2 | `clockspeed/surface/api/contract.py`, `tests/surface/test_contract.py`, `clockspeed/surface/api/solve.py`, `tests/surface/test_solve.py`, `clockspeed/surface/api/power.py`, `tests/surface/test_power.py`, `clockspeed/surface/api/flow_view.py`, `tests/surface/test_flow_view.py` |
| W26-G3-S1 | `README.md`, `tests/test_readme_audit.py` |
| W26-G3-S2 | `clockspeed/advisor/advise.py`, `tests/advisor/test_advise.py` |
| W26-F01 | none |
| W26-F02 | none |
| W26-L01 | `tests/save/test_synthetic.py` |
| W27-G1-S1 | none |
| W27-G1-S2 | `clockspeed/surface/api/registry.py`, `tests/surface/test_registry.py`, `clockspeed/surface/api/map.py`, `clockspeed/surface/api/advice.py`, `clockspeed/surface/web/panel_solve.js`, `tests/surface/test_panel_solve.py` |
| W27-G2-S1 | `tools/action_runtimes.py` |
| W27-G2-S2 | `installer/cli` |
| W27-G3-S1 | `tests/` `test-release_workflow` |
| W27-G3-S2 | none |
| W27-F01 | none |
| W28-G1-S1 | `clockspeed/surface/providers.py`, `tests/surface/test_advice_source.py` |
| W28-G1-S2 | `clockspeed/surface/web/panel_optimize.js`, `tests/surface/test_panel_optimize.py`, `clockspeed/surface/web/panel_power.js`, `tests/surface/test_panel_power.py`, `clockspeed/surface/web/panel_registry.js`, `tests/surface/test_panel_registry.py`, `clockspeed/surface/web/panel_advice.js`, `tests/surface/test_panel_advice.py` |
| W28-G2-S1 | `config/` `runtime_pins`, `tests/` `test-runtime_pins`, `tools/` `runtime_pins` |
| W28-G2-S2 | `tests/advisor/` `test-advise_memo`, `tests/surface/test_advice_source.py`, `clockspeed/advisor/advise.py` |
| W28-G3-S1 | `tests/surface/audit_harness.py`, `tests/surface/golden/advice_no_target.json` |
| W28-G3-S2 | `tools/measurements.json` |
| W28-F01 | none |
| W29-G1-S1 | `clockspeed/data/registry.py`, `tests/data/test_registry.py`, `tests/surface/test_registry.py` |
| W29-G1-S2 | `clockspeed/advisor/ledger.py`, `tests/advisor/test_ledger.py` |
| W29-G2-S1 | `tests/solve/test_phase3_gate.py` |
| W29-G2-S2 | `clockspeed/advisor/advise.py` |
| W29-G3-S1 | `clockspeed/solve/` `staging`, `tests/solve/` `test-staging` |
| W29-G3-S2 | `clockspeed/surface/api/advice.py`, `clockspeed/surface/providers.py`, `tests/surface/test_advice.py`, `tests/surface/test_advice_act.py`, `tests/surface/test_advice_source.py` |
| W29-F01 | none |
| W30-G1-S1 | `clockspeed/advisor/trace.py`, `tests/advisor/test_trace.py` |
| W30-G1-S2 | `clockspeed/surface/web/app.css`, `clockspeed/surface/web/panel_warnings.js`, `tests/surface/test_panel_warnings.py`, `clockspeed/surface/web/panel_unmodelled.js`, `tests/surface/test_panel_unmodelled.py`, `clockspeed/surface/web/` `panel_diagnostics`, `tests/surface/` `test-panel_diagnostics`, `tests/surface/test_web_assets.py` |
| W30-G2-S1 | `clockspeed/surface/web/panel_advice.js`, `clockspeed/surface/web/app.js`, `tests/surface/test_panel_advice.py`, `tests/surface/test_web_assets.py` |
| W30-G2-S2 | `clockspeed/advisor/rules/plan.py`, `tests/advisor/rules/test_plan.py`, `clockspeed/advisor/plans.py`, `tests/advisor/test_plan_redesign.py`, `tests/advisor/test_plan_world.py`, `tests/solve/test_plan_edges.py`, `tests/advisor/test_every_rule_fires.py`, `tests/surface/test_flow_view.py` |
| W30-G3-S1 | `tests/surface/test_advice_golden.py` |
| W30-G3-S2 | `clockspeed/advisor/rules/plan.py`, `tests/advisor/rules/test_plan.py`, `tests/advisor/test_plan_redesign.py`, `tests/advisor/test_plan_world.py`, `tests/surface/test_advice_source.py` |
| W30-F01 | none |
| W30-L01 | `tests/test_edit_lint_check.py`, `tests/conftest.py` |
| W31-G1-S1 | `clockspeed/surface/web/app.css`, `clockspeed/surface/web/panel_solve.js`, `tests/surface/test_panel_solve.py`, `clockspeed/surface/web/panel_optimize.js`, `tests/surface/test_panel_optimize.py`, `clockspeed/surface/web/index.html`, `clockspeed/surface/server.py`, `tests/surface/test_server.py`, `tests/surface/test_web_assets.py`, `tests/surface/test_panel_global_scope.py`, `tests/surface/test_panel_scope.py`, `tests/surface/test_cs1329_driver_timeout.py` |
| W31-G1-S2 | `clockspeed/advisor/ledger.py`, `tests/advisor/test_ledger.py`, `clockspeed/advisor/advise.py`, `tests/advisor/test_advise.py`, `clockspeed/surface/api/advice.py`, `tests/surface/test_advice.py`, `tests/surface/test_advice_act.py`, `tests/surface/test_advice_golden.py`, `tests/surface/golden/advice_no_target.json`, `tests/advisor/test_every_rule_fires.py` |
| W31-G2-S1 | `clockspeed/surface/web/panel_power.js`, `tests/surface/test_panel_power.py`, `clockspeed/surface/server.py`, `tests/surface/test_server.py`, `clockspeed/surface/web/` `panel_console`, `tests/surface/test_advice.py`, `tests/surface/` `test-panel_console`, `clockspeed/surface/web/index.html`, `tests/surface/test_web_assets.py`, `tests/surface/test_panel_global_scope.py`, `clockspeed/surface/web/app.js`, `tests/surface/test_panel_scope.py`, `tests/surface/test_cs1329_driver_timeout.py` |
| W31-G2-S2 | `clockspeed/surface/api/flow_view.py`, `tests/surface/test_flow_view.py` |
| W31-G3-S1 | `clockspeed/advisor/cards.py`, `clockspeed/advisor/rules/fuel.py`, `clockspeed/advisor/rules/plan.py`, `tests/advisor/test_cards.py`, `tests/advisor/test_every_rule_fires.py`, `tests/advisor/rules/test_fuel.py`, `tests/advisor/test_plan_redesign.py`, `tests/advisor/test_plan_redesign_built.py`, `tests/advisor/test_display_name_keying.py`, `tests/advisor/test_trace.py`, `tests/surface/test_advice_source.py` |
| W31-G3-S2 | `clockspeed/save/objects.py` |
| W31-F01 | none |
| W32-G1-S1 | `clockspeed/surface/web/panel_scope.js`, `tests/surface/test_panel_scope.py`, `tests/surface/audit_harness.py`, `tests/ops/test_lane_scope.py` |
| W32-G1-S2 | `clockspeed/surface/web/panel_advice.js`, `tests/surface/test_panel_advice.py`, `clockspeed/surface/web/app.css` |
| W32-G2-S1 | `shell/lib/window.js`, `shell/test/window.test.js`, `shell/main.js`, `tests/shell/test_shell_assets.py`, `docs/adr/0015-the-shell-may-start-the-surface.md` |
| W32-G2-S2 | `clockspeed/surface/web/panel_advice.js`, `tests/surface/test_panel_advice.py`, `tests/surface/test_panel_advice_ui157.py` |
| W32-G3-S1 | `tests/surface/audit_harness.py`, `tests/surface/test_advice_golden.py` |
| W32-G3-S2 | `clockspeed/surface/web/panel_advice.js`, `tests/surface/test_panel_advice.py`, `tests/surface/test_panel_advice_layout.py`, `tests/surface/test_panel_advice_ui157.py` |
| W33-G1-S1 | `clockspeed/advisor/advise.py`, `tests/advisor/test_advise.py`, `clockspeed/advisor/ledger.py`, `tests/advisor/test_ledger.py` |
| W33-G1-S2 | `tests/test_architecture_attributions.py` |
| W33-G2-S1 | `clockspeed/advisor/rules/power.py`, `tests/advisor/rules/test_power.py`, `clockspeed/advisor/rules/fuel.py`, `tests/advisor/rules/test_fuel.py`, `tests/advisor/test_advise.py`, `tests/advisor/test_ledger.py`, `tests/advisor/test_cards.py`, `tests/advisor/test_world_advice.py` |
| W33-G2-S2 | `clockspeed/surface/providers.py`, `clockspeed/surface/api/advice.py`, `tests/surface/test_advice_act.py`, `tests/surface/test_advice_source.py`, `tests/surface/test_advice_aging.py`, `tests/surface/test_advice.py`, `tests/surface/audit_harness.py` |
| W33-G3-S1 | `clockspeed/advisor/rules/plan.py`, `tests/advisor/rules/test_plan.py`, `clockspeed/advisor/cards.py`, `tests/advisor/test_cards.py` |
| W33-G3-S2 | `clockspeed/surface/web/app.js`, `clockspeed/surface/web/panel_advice.js`, `tests/surface/test_panel_advice.py`, `tests/surface/test_web_assets.py` |
| W33-F01 | none |
| W33-F02 | none |
| W33-F03 | none |
| W33-L01 | `tests/save/test_properties.py`, `tests/save/test_value_anchoring.py` |
| W34-G1-S1 | none |
| W34-G1-S2 | `clockspeed/surface/api/advice.py`, `tests/surface/test_advice.py`, `tests/surface/golden/advice_no_target.json`, `tests/surface/test_panel_advice.py`, `tests/surface/audit_harness.py` |
| W34-G2-S1 | `clockspeed/surface/web/` `panel_play`, `tests/surface/` `test-panel_play` |
| W34-G2-S2 | `clockspeed/surface/api/` `plan`, `tests/surface/` `test-plan`, `tests/surface/` `test-numeric_schema` |
| W34-G3-S1 | `tests/advisor/test_every_rule_fires.py` |
| W34-G3-S2 | `clockspeed/audit/balance.py`, `tests/audit/test_balance.py`, `clockspeed/audit/__init__.py`, `clockspeed/advisor/rules/power.py`, `tests/advisor/rules/test_power.py`, `tests/audit/test_package_exports.py`, `tests/audit/test_every_warning_fires.py`, `tests/repr_rendering_guard.py` |
| W34-F01 | none |
| W35-G1-S1 | `clockspeed/advisor/plans.py`, `clockspeed/advisor/rules/plan.py`, `tests/advisor/rules/test_plan.py`, `tests/advisor/test_plan_world.py`, `tests/advisor/test_every_rule_fires.py`, `tests/solve/test_plan_edges.py`, `tests/surface/test_flow_view.py` |
| W35-G1-S2 | `clockspeed/audit/overlay.py` |
| W35-G2-S1 | `clockspeed/advisor/trace.py`, `clockspeed/advisor/advise.py` |
| W35-G2-S2 | `clockspeed/solve/optimize.py`, `tests/solve/test_optimize.py` |
| W35-G3-S1 | `clockspeed/advisor/ranking.py`, `clockspeed/surface/api/flow_view.py`, `tests/surface/test_flow_view.py`, `tests/surface/` `test-numeric_schema` |
| W35-G3-S2 | `tests/surface/test_advice_source.py` |
| W35-F01 | none |
| W36-G1-S1 | `clockspeed/surface/web/panel_advice.js`, `tests/surface/test_panel_advice.py`, `tests/advisor/test_plan_world.py` |
| W36-G1-S2 | none |
| W36-G2-S1 | `tests/surface/test_advice_golden.py`, `tests/surface/golden/advice_no_target.json` |
| W36-G2-S2 | `tools/dashboard_probe.py`, `tests/test_dashboard_probe.py` |
| W36-G3-S1 | `clockspeed/surface/web/` `panel_play`, `tests/surface/` `test-panel_play` |
| W36-G3-S2 | none |
| W36-L01 | `tests/surface/test_server.py` |
| W37-G1-S1 | `clockspeed/advisor/plans.py`, `clockspeed/advisor/rules/plan.py`, `clockspeed/surface/api/flow_view.py`, `clockspeed/surface/web/panel_advice.js`, `tests/advisor/test_plan_world.py`, `tests/advisor/rules/test_plan.py`, `tests/surface/test_flow_view.py`, `tests/surface/test_panel_advice.py`, `tests/surface/test_advice_golden.py`, `tests/solve/test_plan_edges.py`, `tests/surface/golden/advice_no_target.json` |
| W37-G1-S2 | `clockspeed/surface/web/` `panel_play`, `tests/surface/` `test-panel_play`, `tests/surface/test_web_assets.py`, `clockspeed/surface/web/app.js`, `clockspeed/surface/web/app.css` |
| W37-G2-S1 | `clockspeed/advisor/plans.py`, `clockspeed/advisor/rules/plan.py`, `tests/advisor/rules/test_plan.py`, `tests/solve/test_plan_edges.py` |
| W37-G2-S2 | none |
| W37-G3-S1 | `tests/surface/test_world.py`, `tests/surface/audit_harness.py`, `clockspeed/surface/api/world.py`, `tests/ops/test_lane_scope.py` |
| W37-G3-S2 | `shell/lib/trust.js`, `shell/lib/verdict.js`, `shell/test/trust.test.js`, `shell/test/verdict.test.js`, `docs/adr/0014-the-shell-trusts-one-pinned-certificate.md`, `shell/main.js` |
| W37-F01 | none |
| W37-F02 | none |
| W38-G1-S1 | `tests/surface/test_advice_golden.py`, `tests/advisor/test_plan_world.py`, `tests/surface/golden/advice_no_target.json` |
| W38-G1-S2 | `clockspeed/surface/web/index.html`, `clockspeed/surface/web/app.css`, `clockspeed/surface/server.py`, `tests/surface/test_server.py`, `tests/surface/test_web_assets.py`, `clockspeed/surface/api/` `audit`, `tests/surface/` `test-audit`, `clockspeed/surface/web/app.js`, `tests/surface/audit_harness.py` |
| W38-G2-S1 | `clockspeed/advisor/trace.py`, `tests/advisor/test_trace.py`, `clockspeed/advisor/advise.py`, `clockspeed/audit/overlay.py`, `tests/audit/test_overlay.py` |
| W38-G2-S2 | `clockspeed/surface/web/app.css`, `clockspeed/surface/web/` `panel_play`, `tests/surface/` `test-panel_play`, `tests/surface/test_web_assets.py` |
| W38-G3-S1 | `clockspeed/surface/api/` `overlay`, `tests/surface/` `test-overlay` |
| W38-G3-S2 | `shell/test/window.test.js`, `shell/lib/window.js`, `shell/main.js`, `tests/shell/test_shell_assets.py` |
| W38-F01 | none |
| W38-F02 | none |
| W39-G1-S1 | `clockspeed/surface/api/routes.py`, `tests/surface/test_routes.py`, `clockspeed/surface/providers.py`, `clockspeed/surface/api/health.py`, `tests/surface/test_health.py`, `clockspeed/surface/web/app.js`, `tests/surface/test_web_assets.py`, `tests/surface/test_acceptance.py`, `tests/surface/test_server.py`, `tests/surface/` `test-overlay` |
| W39-G1-S2 | `clockspeed/advisor/advise.py`, `tests/advisor/test_advise.py` |
| W39-G2-S1 | `clockspeed/advisor/plans.py`, `clockspeed/advisor/rules/plan.py`, `clockspeed/advisor/advise.py`, `tests/advisor/rules/test_plan.py`, `tests/surface/test_advice_golden.py` |
| W39-G2-S2 | `clockspeed/surface/web/app.css`, `clockspeed/surface/web/app.js`, `clockspeed/surface/web/` `panel_play`, `tests/surface/` `test-panel_play`, `tests/surface/test_web_assets.py`, `tools/dashboard_probe.py`, `tests/test_dashboard_probe.py` |
| W39-G3-S1 | `clockspeed/surface/api/flow_view.py`, `tests/surface/test_flow_view.py` |
| W39-G3-S2 | `shell/lib/state.js`, `shell/test/state.test.js`, `shell/lib/window.js`, `shell/test/window.test.js` |
| W39-F01 | none |
| W40-G1-S1 | `clockspeed/surface/api/advice.py`, `tests/surface/test_advice.py`, `clockspeed/surface/web/panel_advice.js`, `tests/surface/test_panel_advice.py`, `tests/surface/audit_harness.py`, `tests/surface/test_flow_view.py` |
| W40-G1-S2 | `tools/measurements.json` |
| W40-G2-S1 | `clockspeed/surface/providers.py`, `clockspeed/surface/web/app.js`, `clockspeed/surface/api/routes.py`, `clockspeed/surface/api/health.py`, `tests/surface/test_health.py`, `tests/surface/test_routes.py`, `tests/surface/test_acceptance.py`, `tests/surface/audit_harness.py`, `tests/surface/test_web_assets.py`, `clockspeed/surface/web/` `panel_diagnostics` |
| W40-G2-S2 | none |
| W40-G3-S1 | `clockspeed/audit/network.py`, `tests/audit/test_network.py` |
| W40-F01 | none |
| W40-L01 | `tests/ops/test_queue_lane_relaunch.py` |
| W41-G1-S1 | `clockspeed/surface/api/advice.py`, `tests/surface/test_advice.py`, `tests/surface/audit_harness.py`, `tests/surface/test_web_assets.py`, `tests/surface/golden/advice_no_target.json`, `tests/surface/test_advice_golden.py`, `tests/surface/test_panel_advice.py` |
| W41-G1-S2 | `clockspeed/audit/inventory.py`, `tests/audit/test_inventory.py` |
| W41-G2-S1 | `shell/lib/tray.js`, `shell/test/tray.test.js` |
| W41-G2-S2 | `clockspeed/solve/ratio.py`, `tests/solve/test_ratio.py` |
| W41-G3-S1 | `shell/main.js`, `tests/shell/test_shell_assets.py` |
| W41-G3-S2 | none |
| W41-F01 | none |
| W42-G1-S1 | none |
| W42-G1-S2 | `docs/adr/0019-the-map-underlay-and-the-purity-declaration.md` |
| W42-G2-S1 | `clockspeed/advisor/rules/__init__.py`, `clockspeed/advisor/ranking.py`, `clockspeed/advisor/advise.py`, `tests/advisor/test_every_rule_fires.py`, `tests/advisor/test_world_advice.py`, `tests/surface/test_advice_source.py` |
| W42-G2-S2 | `clockspeed/surface/api/map.py`, `clockspeed/audit/__init__.py`, `tests/surface/test_map.py`, `tests/audit/test_package_exports.py`, `tests/test_repr_rendering.py` |
| W42-G3-S1 | `tests/solve/synthetic.py`, `tests/ops/test_lane_scope.py` |
| W42-G3-S2 | `clockspeed/save/usmap.py`, `tests/save/test_usmap.py` |
| W42-F01 | none |
| W42-F02 | none |
| W42-F03 | none |
| W43-G1-S1 | `clockspeed/surface/api/map.py`, `tests/surface/test_map.py`, `tests/surface/audit_harness.py`, `tests/surface/test_panel_map.py` |
| W43-G1-S2 | `shell/lib/window.js`, `shell/test/window.test.js`, `shell/main.js`, `tests/shell/test_shell_assets.py`, `shell/lib/` `wiring`, `shell/test/` `wiring.test` |
| W43-G2-S1 | `clockspeed/surface/web/app.js`, `tests/surface/test_web_assets.py`, `tests/surface/` `test-views` |
| W43-G2-S2 | `clockspeed/audit/placement.py`, `clockspeed/audit/inventory.py`, `clockspeed/audit/balance.py`, `clockspeed/audit/footprint.py`, `clockspeed/audit/flow.py`, `clockspeed/audit/fuel.py`, `clockspeed/audit/machines.py`, `clockspeed/audit/__init__.py`, `tests/audit/test_package_exports.py`, `tests/ops/test_lane_scope.py` |
| W43-G3-S1 | `clockspeed/advisor/cards.py`, `clockspeed/advisor/rules/fuel.py`, `clockspeed/advisor/rules/plan.py`, `tests/advisor/test_cards.py`, `tests/advisor/test_every_rule_fires.py`, `tests/advisor/rules/test_fuel.py`, `tests/advisor/test_plan_redesign.py`, `tests/advisor/test_plan_redesign_built.py`, `tests/advisor/test_display_name_keying.py`, `tests/advisor/test_trace.py`, `tests/surface/test_advice_source.py` |
| W43-G3-S2 | `clockspeed/save/objects.py`, `tests/save/test_objects.py` |
| W43-L01 | `tests/ops/test_driver_module_binding.py` |
| W44-G1-S1 | `clockspeed/surface/web/panel_map.js`, `tests/surface/test_panel_map.py`, `tests/surface/panel_harness.py` |
| W44-G1-S2 | none |
| W44-G2-S1 | `clockspeed/surface/web/app.css` |
| W44-G2-S2 | `clockspeed/surface/api/advice.py`, `tests/surface/test_advice.py`, `clockspeed/surface/api/routes.py`, `clockspeed/surface/api/health.py`, `clockspeed/surface/providers.py`, `clockspeed/surface/web/app.js`, `tests/surface/test_advice_source.py`, `tests/surface/test_health.py`, `tests/surface/test_routes.py`, `tests/surface/test_acceptance.py`, `tests/surface/test_pending.py`, `tests/surface/test_web_assets.py`, `tests/surface/audit_harness.py` |
| W44-G3-S1 | `tests/surface/audit_harness.py`, `tests/surface/test_web_assets.py` |
| W45-G1-S1 | none |
| W45-G1-S2 | `clockspeed/surface/web/app.js`, `clockspeed/surface/web/app.css`, `tests/surface/test_web_assets.py`, `clockspeed/surface/web/index.html`, `tests/surface/test_panel_seam.py`, `tests/surface/panel_harness.py`, `tests/surface/test_panel_advice.py`, `tests/surface/test_panel_global_scope.py` |
| W45-G2-S1 | none |
| W45-G2-S2 | `clockspeed/surface/web/` `panel_plan`, `tests/surface/` `test-panel_plan`, `clockspeed/surface/web/app.js`, `tests/surface/test_panel_scope.py`, `tests/surface/test_panel_seam.py`, `clockspeed/surface/server.py`, `clockspeed/surface/web/index.html`, `tests/surface/test_web_assets.py`, `tests/surface/test_server.py` |
| W45-G3-S1 | `clockspeed/surface/server.py`, `tests/surface/test_server.py` |
| W45-G3-S2 | `clockspeed/advisor/advise.py`, `tests/advisor/rules/` `test-production`, `tests/advisor/test_world_advice.py` |
| W45-F01 | none |
| W46-G1-S1 | `clockspeed/surface/web/index.html`, `clockspeed/surface/web/app.js` |
| W46-G1-S2 | `clockspeed/advisor/ranking.py`, `tests/advisor/test_ranking.py`, `tests/advisor/test_every_rule_fires.py`, `clockspeed/advisor/rules/__init__.py`, `tests/advisor/test_world_advice.py`, `tests/surface/golden/advice_no_target.json` |
| W46-G2-S1 | `clockspeed/surface/providers.py`, `tests/surface/test_web_assets.py`, `tests/surface/test_panel_scope.py`, `tests/surface/` `test-views` |
| W46-G2-S2 | `clockspeed/surface/web/panel_advice.js`, `tests/surface/test_panel_advice.py` |
| W46-G3-S1 | `tests/ops/test_lane_scope.py` |
| W46-G3-S2 | `tests/advisor/worlds.py`, `tests/advisor/test_world_advice.py` |
| W46-L01 | `tests/save/test_independent_table.py`, `tests/save/independent_table.py` |
| W47-G1-S1 | `clockspeed/surface/web/panel_registry.js`, `tests/surface/test_panel_registry.py` |
| W47-G1-S2 | `clockspeed/audit/network.py`, `tests/audit/test_network.py`, `clockspeed/audit/machines.py`, `clockspeed/audit/__init__.py`, `tests/audit/test_package_exports.py`, `tests/audit/test_machines.py`, `tests/audit/test_balance.py`, `tests/audit/test_every_warning_fires.py` |
| W47-G2-S1 | `clockspeed/surface/providers.py`, `tests/surface/test_panel_advice.py`, `clockspeed/surface/api/advice.py`, `clockspeed/surface/web/app.js`, `tests/surface/test_advice.py`, `tests/surface/test_advice_source.py`, `tests/surface/audit_harness.py`, `tests/surface/golden/advice_no_target.json`, `tests/surface/test_web_assets.py` |
| W47-G2-S2 | none |
| W47-G3-S1 | `clockspeed/audit/__init__.py`, `clockspeed/audit/balance.py`, `tests/audit/test_balance.py`, `tests/audit/test_package_exports.py` |
| W47-G3-S2 | `clockspeed/surface/` `oplog`, `tests/surface/test_server.py` |
| W47-F01 | none |
| W48-G1-S1 | `clockspeed/surface/web/app.css`, `clockspeed/surface/web/panel_advice.js`, `tests/surface/test_panel_advice.py`, `tests/surface/test_panel_advice_layout.py`, `clockspeed/surface/web/app.js` |
| W48-G1-S2 | `clockspeed/data/schematics.py`, `tests/data/test_schematics.py`, `tests/solve/test_phase3_gate.py` |
| W48-G2-S1 | `clockspeed/surface/web/panel_advice.js`, `clockspeed/surface/web/app.css`, `tests/surface/test_panel_advice.py` |
| W48-G2-S2 | `tests/solve/test_phase3_gate.py` |
| W48-G3-S1 | `clockspeed/surface/` `oplog`, `tests/surface/test_server.py` |
| W48-G3-S2 | `tests/surface/test_panel_advice_layout.py`, `clockspeed/surface/web/panel_advice.js`, `clockspeed/surface/web/panel_registry.js`, `clockspeed/surface/web/app.css`, `tests/surface/test_panel_advice.py`, `tests/surface/test_panel_registry.py` |
| W48-F01 | none |
| W49-G1-S1 | `clockspeed/advisor/rules/__init__.py`, `clockspeed/advisor/ranking.py`, `tests/advisor/test_ranking.py`, `clockspeed/advisor/advise.py`, `clockspeed/save/world.py`, `tests/save/test_world.py`, `tests/advisor/test_world_advice.py`, `tests/advisor/test_every_rule_fires.py` |
| W49-G1-S2 | none |
| W49-G2-S1 | `clockspeed/advisor/advise.py`, `tests/advisor/rules/` `test-materials`, `tests/advisor/test_display_name_keying.py` |
| W49-G2-S2 | `clockspeed/save/world.py`, `tests/save/test_world.py`, `clockspeed/audit/` `siting`, `tests/audit/` `test-siting`, `clockspeed/advisor/rules/` `siting`, `tests/advisor/rules/` `test-siting`, `tests/advisor/test_every_rule_fires.py` |
| W49-G3-S1 | `clockspeed/save/objects.py`, `tests/save/test_properties.py` |
| W49-F01 | none |
| W50-G1-S1 | `clockspeed/advisor/ranking.py`, `clockspeed/advisor/rules/__init__.py`, `tests/advisor/test_every_rule_fires.py`, `tests/advisor/rules/` `test-materials`, `tests/surface/test_schematic_source.py`, `tests/advisor/test_plan_world.py`, `tests/advisor/test_display_name_keying.py`, `tests/surface/test_advice_act.py`, `tests/surface/test_advice_source.py` |
| W50-G1-S2 | `clockspeed/surface/web/app.css`, `clockspeed/surface/web/panel_advice.js`, `tests/surface/test_web_assets.py`, `tests/surface/test_panel_advice.py`, `tests/surface/test_flow_view.py`, `tests/surface/test_panel_advice_ui157.py` |
| W50-G2-S1 | `clockspeed/advisor/rules/` `production`, `tests/advisor/rules/` `test-production`, `clockspeed/advisor/advise.py`, `tests/advisor/test_advise.py`, `clockspeed/advisor/ranking.py`, `tests/advisor/test_every_rule_fires.py`, `tests/advisor/test_ranking.py` |
| W50-G2-S2 | `clockspeed/surface/` `oplog`, `tests/surface/` `test-oplog_rotation`, `tests/surface/test_server.py` |
| W50-G3-S1 | `tests/advisor/test_plan_world.py` |
| W50-G3-S2 | `tests/save/test_oracle_citations.py`, `tests/save/test_absolute_claims.py` |
| W50-F01 | none |
| W50-F02 | none |
| W50-L01 | `tests/test_queue_loop_ci_specs.py`, `tests/test_tier1_budget.py` |
| W51-G1-S1 | `clockspeed/surface/api/world.py`, `tests/surface/test_world.py`, `clockspeed/advisor/plans.py`, `clockspeed/surface/api/routes.py`, `tests/surface/audit_harness.py`, `clockspeed/surface/web/panel_scope.js`, `tests/surface/test_panel_scope.py` |
| W51-G1-S2 | `clockspeed/surface/config.py`, `tests/surface/test_config.py`, `clockspeed/surface/__main__.py`, `tests/surface/test_routes.py`, `tests/surface/test_schematic_source.py` |
| W51-G2-S1 | `tests/surface/test_panel_advice.py`, `clockspeed/surface/api/registry.py`, `tests/surface/test_registry.py`, `tests/surface/audit_harness.py` |
| W51-G2-S2 | `clockspeed/save/sightings.py`, `tests/save/test_sightings.py`, `clockspeed/surface/providers.py`, `clockspeed/progress/` `delta`, `tests/progress/` `test-delta`, `tests/surface/test_world_provider_memo.py` |
| W51-G3-S1 | `clockspeed/surface/server.py`, `tests/surface/test_server.py` |
| W51-G3-S2 | `clockspeed/surface/web/app.css`, `clockspeed/surface/web/app.js`, `clockspeed/surface/web/index.html`, `clockspeed/surface/web/panel_advice.js`, `tests/surface/test_web_assets.py`, `tests/surface/test_panel_advice.py`, `tests/surface/audit_harness.py`, `clockspeed/surface/web/panel_registry.js`, `tests/surface/test_panel_registry.py` |
| W51-F01 | none |
| W52-G1-S1 | `clockspeed/advisor/rules/__init__.py`, `clockspeed/advisor/advise.py`, `clockspeed/advisor/ranking.py`, `tests/advisor/test_every_rule_fires.py`, `tests/advisor/worlds.py`, `tests/advisor/test_advise.py`, `tests/advisor/test_world_advice.py` |
| W52-G1-S2 | `clockspeed/surface/api/registry.py`, `clockspeed/surface/web/panel_registry.js`, `tests/data/test_docs_extract.py` |
| W52-G2-S1 | `tests/surface/test_acceptance.py`, `clockspeed/surface/web/panel_advice.js`, `tests/surface/test_panel_advice.py` |
| W52-G2-S2 | `clockspeed/surface/web/app.css`, `tests/surface/test_web_assets.py` |
| W52-F01 | none |
| W53-G1-S1 | `clockspeed/surface/providers.py`, `tests/surface/` `test-oplog` |
| W53-G1-S2 | `clockspeed/surface/web/app.css`, `clockspeed/surface/web/panel_registry.js`, `tests/surface/test_web_assets.py`, `tests/surface/test_panel_registry.py` |
| W53-G2-S1 | `shell/lib/endpoint.js`, `shell/test/endpoint.test.js`, `tests/shell/test_shell_assets.py` |
| W53-G2-S2 | `tests/audit/` `test-network_edges`, `tests/audit/test_every_warning_fires.py`, `tests/audit/` `test-network_library`, `clockspeed/audit/network.py`, `clockspeed/audit/__init__.py`, `tests/audit/test_package_exports.py` |
| W53-G3-S1 | `clockspeed/surface/web/` `panel_console`, `tests/surface/` `test-panel_console`, `clockspeed/surface/web/panel_scope.js`, `tests/surface/test_panel_scope.py` |
| W53-G3-S2 | `clockspeed/surface/api/advice.py`, `clockspeed/surface/providers.py`, `tests/surface/test_advice.py`, `tests/surface/test_advice_source.py`, `tests/surface/audit_harness.py`, `tests/surface/golden/advice_no_target.json`, `clockspeed/surface/web/panel_advice.js`, `tests/surface/test_panel_advice.py` |
| W53-F01 | none |
| W53-L01 | `tests/save/test_struct_controls.py` |
| W54-G1-S1 | `shell/lib/` `oplog`, `shell/test/` `oplog.test`, `shell/lib/endpoint.js`, `shell/test/endpoint.test.js`, `tests/shell/` `test-oplog_binding`, `tests/shell/test_shell_assets.py` |
| W54-G1-S2 | `clockspeed/advisor/ledger.py`, `tests/advisor/test_ledger.py` |
| W54-G2-S1 | `tests/shell/` `test-oplog_binding`, `shell/main.js`, `tests/shell/test_shell_assets.py` |
| W54-G2-S2 | `clockspeed/surface/api/advice.py`, `clockspeed/surface/providers.py`, `clockspeed/surface/__main__.py`, `clockspeed/surface/api/contract.py`, `tests/surface/test_advice_act.py`, `tests/surface/test_contract.py`, `tests/surface/test_schematic_source.py`, `tests/surface/test_routes.py` |
| W54-G3-S1 | `clockspeed/surface/web/panel_advice.js`, `tests/surface/test_panel_advice.py` |
| W54-F01 | none |
| W54-F02 | none |
| W55-G1-S1 | none |
| W55-G1-S2 | `shell/main.js`, `tests/shell/test_shell_assets.py` |
| W55-G2-S1 | `clockspeed/surface/` `diagnostics`, `tests/surface/` `test-diagnostics` |
| W55-G2-S2 | none |
| W55-G3-S1 | `tests/shell/test_shell_assets.py` |
| W55-G3-S2 | `clockspeed/surface/server.py`, `tests/surface/test_server.py` |
| W55-F01 | none |
| W55-F02 | none |
| W55-F03 | none |
| W56-G1-S1 | `clockspeed/save/world.py`, `tests/save/test_world.py`, `tests/save/synthetic.py` |
| W56-G1-S2 | `docs/adr/` `NNNN-the-oodle-data-licence-verdict` |
| W56-G2-S1 | `shell/lib/` `diagnostics`, `shell/test/` `diagnostics.test` |
| W56-G2-S2 | `clockspeed/surface/server.py`, `tools/measurements.json`, `tests/surface/test_server.py` |
| W56-G3-S1 | `shell/main.js`, `tests/shell/test_shell_assets.py`, `shell/lib/` `diagnostics`, `shell/test/` `diagnostics.test` |
| W56-G3-S2 | `clockspeed/surface/api/contract.py`, `clockspeed/surface/server.py`, `tests/surface/test_contract.py`, `tests/surface/test_server.py`, `tests/surface/` `test-connection_discipline` |
| W56-F01 | none |
| W56-F02 | none |
| W56-L01 | `tests/save/test_decode_oracles.py` |
| W57-G1-S1 | `clockspeed/surface/providers.py`, `tests/surface/test_web_assets.py` |
| W57-G1-S2 | `shell/main.js`, `shell/lib/window.js`, `shell/test/window.test.js`, `tests/shell/test_shell_assets.py` |
| W57-G2-S1 | `tools/measurements.json` |
| W57-G2-S2 | `tests/surface/` `test-diagnostics_redaction` |
| W57-G3-S1 | `clockspeed/data/locate.py`, `tests/data/test_locate.py`, `clockspeed/save/workdir.py`, `tests/save/test_workdir.py`, `scripts/verify_env.py`, `tests/test_verify_env.py`, `tools/facts_probe.py`, `tests/test_facts_probe.py`, `tools/flip_checks.py`, `tests/test_flip_checks.py` |
| W57-G3-S2 | `clockspeed/save/objects.py` |
| W58-G1-S1 | `tests/data/test_phase2_gate.py`, `tests/save/reach_guard.py`, `tests/save/test_reach_guard.py`, `tests/save/test_phase4_gate.py`, `tests/save/test_phase4_gate_depth.py`, `tests/save/test_properties.py`, `tests/save/test_objects.py`, `tests/save/test_world.py`, `tests/save/test_synthetic.py`, `tests/save/test_trailing_run.py` |
| W58-G1-S2 | `clockspeed/save/objects.py`, `clockspeed/save/world.py` |
| W58-G2-S1 | `clockspeed/data/registry.py`, `tests/data/test_registry.py`, `clockspeed/data/version.py`, `clockspeed/data/docs_extract.py` |
| W58-G2-S2 | `tests/save/test_item_list.py`, `tests/save/test_reference_list.py`, `tests/save/test_reference_pair.py`, `tests/save/test_transform_list.py`, `tests/save/test_struct_interior_14_60.py`, `tests/advisor/test_plan_world.py`, `tests/assertion_rendering_guard.py`, `tests/test_assertion_rendering.py`, `tests/test_hook_env_echo.py` |
| W58-G3-S1 | `clockspeed/save/objects.py`, `clockspeed/save/world.py`, `tests/save/test_world.py`, `tests/save/synthetic.py` |
| W58-G3-S2 | `tests/save/test_struct_interior.py`, `tests/data/test_phase2_gate.py`, `tests/test_citation_tables.py`, `tests/test_assertion_rendering.py` |
| W59-G1-S1 | `clockspeed/save/objects.py`, `tests/save/test_properties.py` |
| W59-G1-S2 | `scripts/verify_env.py`, `tests/test_verify_env.py`, `clockspeed/data/locate.py`, `tests/data/test_locate.py` |
| W59-G2-S1 | `clockspeed/save/objects.py` |
| W59-G2-S2 | none |
| W59-G3-S1 | `tests/save/synthetic.py` |
| W59-G3-S2 | `tests/save/test_world.py`, `tests/data/test_phase2_gate.py`, `tests/test_exception_rendering.py`, `tests/test_citation_tables.py` |
| W59-L01 | `tests/ops/test_lane_scope.py` |
| W60-G1-S1 | `clockspeed/save/chunks.py`, `tests/save/test_chunks.py`, `clockspeed/save/objects.py`, `tests/save/test_objects.py` |
| W60-G1-S2 | `tests/save/test_phase4_gate_depth.py`, `tests/save/test_inventory_item.py`, `tests/save/test_struct_interior.py`, `tests/save/test_struct_interior_14_60.py`, `tests/save/test_element_framing_refusals.py`, `tests/save/test_properties.py` |
| W60-G2-S1 | `tests/save/test_struct_interior.py` |
| W60-G2-S2 | `clockspeed/save/world.py`, `tests/save/test_container_elements.py` |
| W60-G3-S1 | `tests/save/test_property_payload_14_60.py`, `clockspeed/save/objects.py`, `tests/save/synthetic.py` |
| W60-G3-S2 | `clockspeed/save/workdir.py`, `tests/save/test_workdir.py` |
| W60-L01 | `tests/save/test_phase4_gate.py` |
| W61-G1-S1 | `clockspeed/save/header.py`, `tests/save/test_header.py`, `clockspeed/save/world.py`, `tests/save/test_world.py`, `tests/save/test_properties.py` |
| W61-G1-S2 | `clockspeed/data/locate.py`, `tests/data/test_locate.py`, `tests/data/test_phase2_gate.py`, `scripts/verify_env.py`, `tools/facts_probe.py`, `tools/flip_checks.py`, `tests/test_verify_env.py`, `tests/test_facts_probe.py` |
| W61-G2-S1 | `clockspeed/save/world.py`, `tests/test_docs_citations.py` |
| W61-G2-S2 | `clockspeed/save/objects.py`, `tests/save/synthetic.py` |
| W61-G3-S1 | `clockspeed/save/objects.py`, `tests/save/test_trailing_run.py` |
| W61-G3-S2 | `docs/adr/0016-unlock-arrays-carriers-and-serialized-grammar.md` |
| W62-G1-S1 | `clockspeed/data/locate.py`, `tests/data/test_locate.py` |
| W62-G1-S2 | `clockspeed/save/world.py`, `tests/save/test_world.py` |
| W62-G2-S1 | `clockspeed/data/locate.py`, `tests/data/test_locate.py`, `clockspeed/save/workdir.py`, `tests/save/test_workdir.py`, `tests/save/reach_guard.py` |
| W62-G2-S2 | `tests/save/independent_table.py` |
| W62-G3-S1 | none |
| W62-G3-S2 | `clockspeed/data/locate.py`, `clockspeed/save/objects.py` |
| W63-G1-S1 | `tests/save/test_struct_interior.py`, `tests/save/synthetic.py` |
| W63-G1-S2 | `tests/save/test_properties.py`, `tests/data/test_phase2_gate.py`, `tests/test_citation_tables.py`, `tests/test_assertion_rendering.py`, `tests/test_exception_rendering.py`, `tests/test_disposition_sites.py` |
| W63-G2-S1 | `docs/adr/0016-unlock-arrays-carriers-and-serialized-grammar.md`, `clockspeed/save/world.py`, `tests/save/test_world.py`, `tests/save/synthetic.py`, `clockspeed/progress/milestones.py` |
| W63-G2-S2 | `tests/test_architecture_attributions.py`, `tests/save/test_independent_table.py` |
| W63-G3-S1 | `tests/test_headless_queue_prompt.py`, `tests/save/test_phase4_gate.py` |
| W63-G3-S2 | `tests/conftest.py`, `tests/test_report_redaction_classes.py` |
| W63-L01 | `tests/ops/test_queue_lane_relaunch.py` |
| W64-G1-S1 | `tests/save/test_decode_oracles.py`, `tests/save/test_struct_controls.py`, `tests/save/test_container_elements.py`, `tests/save/test_inventory_potential.py` |
| W64-G1-S2 | `tests/test_hook_interpreter_ladder.py`, `tests/test_scaffold.py` |
| W64-G2-S1 | `tests/save/test_width_rule.py`, `tests/save/test_byte_order_status.py`, `tests/save/test_struct_interior.py` |
| W64-G2-S2 | `tests/solve/test_phase3_gate.py`, `tests/data/test_phase2_gate.py` |
| W64-G3-S1 | `clockspeed/save/objects.py`, `tests/save/test_objects.py`, `tests/save/synthetic.py` |
| W64-G3-S2 | `tests/conftest.py`, `tests/test_liveness.py`, `tests/liveness.py`, `tests/test_archive_rot.py`, `tests/test_docs_citations.py`, `tests/assertion_rendering_guard.py`, `tests/bare_path_guard.py`, `tests/chained_cause_guard.py`, `tests/chained_exemption_guard.py` |
| W65-G1-S1 | `tests/save/test_value_anchoring.py`, `tests/save/test_properties.py`, `clockspeed/save/objects.py`, `tests/save/reach_guard.py` |
| W65-G1-S2 | `tests/exception_message_guard.py`, `tests/locals_rendering_guard.py`, `tests/repr_rendering_guard.py`, `tests/secret_sweep_guard.py`, `tests/sphinx_role_guard.py`, `tests/toolpath_guard.py`, `tests/data/test_drift_guard_data.py`, `tests/ops/test_headless_spawn_paths.py`, `tests/ops/test_lane_background_tasks.py`, `tests/shell/test_shell_assets.py`, `tests/solve/test_ceiling_fence.py` |
| W65-G2-S1 | `tools/inbox_watch.py`, `tests/test_inbox_watch.py` |
| W65-G2-S2 | `tests/test_docs_citations.py`, `tests/test_citation_tables.py` |
| W65-G3-S1 | `tests/assertion_rendering_guard.py`, `tests/save/test_value_anchoring.py` |
| W65-G3-S2 | `tools/drift_guard.py`, `tests/data/test_drift_guard_data.py` |
| W66-G1-S1 | `ops/loop/lanes.py`, `ops/loop/winmutex.py` |
| W66-G1-S2 | `tests/sphinx_role_guard.py`, `tests/test_sphinx_roles.py` |
| W66-G2-S1 | `tests/save/test_world.py`, `tests/save/test_properties.py` |
| W66-G2-S2 | `tests/repr_rendering_guard.py`, `tests/test_repr_rendering.py`, `tests/exception_message_guard.py`, `tests/test_exception_messages.py` |
| W66-G3-S1 | none |
| W66-G3-S2 | `ops/loop/lane_launcher.py`, `tests/test_lane_launcher.py`, `ops/loop/queue_loop.py`, `tests/test_lane_lock.py` |
| W66-L01 | `tests/ops/test_multi_lane.py` |
| W67-G1-S1 | `tests/test_handler_exception_rendering.py`, `tests/locals_rendering_guard.py` |
| W67-G1-S2 | `tests/solve/test_optimize.py`, `tests/save/test_header.py` |
| W67-G2-S1 | `tests/toolpath_guard.py` |
| W67-G2-S2 | `clockspeed/save/objects.py` |
| W67-G3-S1 | `tests/test_redaction_scope.py`, `tests/save/test_absolute_claims.py` |
| W67-G3-S2 | `tests/surface/test_acceptance.py`, `tests/test_citation_tables.py`, `tests/test_exception_rendering.py`, `tests/test_flip_checks.py`, `tests/test_handler_exception_rendering.py`, `tests/test_hook_file_mode.py`, `tests/test_lane_lock.py`, `tests/test_provenance_manifest.py`, `tests/test_readme_audit.py`, `tests/test_subprocess_timeouts.py`, `tests/test_third_party_register.py` |
| W68-G1-S1 | `tests/bare_path_guard.py`, `tests/test_docs_citations.py`, `tests/test_bare_path_citations.py` |
| W68-G1-S2 | `tests/test_memory_sync_link_derivation.py` |
| W68-G2-S1 | `tests/save/reach_guard.py`, `tests/save/test_reach_guard.py`, `tests/save/test_properties.py`, `tests/save/test_collectables.py`, `tests/save/test_item_list.py`, `tests/save/test_objects.py`, `tests/save/test_phase4_gate.py`, `tests/save/test_phase4_gate_depth.py` |
| W68-G2-S2 | `tests/conftest.py` |
| W68-G3-S1 | `tests/test_toolpath.py`, `tests/test_make_cert.py`, `tests/test_make_shortcut.py` |
| W68-G3-S2 | `tools/drift_guard.py`, `tools/memory_sync.py`, `tests/data/test_drift_guard_data.py`, `tests/test_memory_sync_link_derivation.py` |
| W69-G1-S1 | `tests/data/test_item_notes_index.py`, `docs/adr/0022-acceptance-lives-in-the-item-note.md` |
| W69-G1-S2 | `tests/save/test_trailing_run.py` |
| W69-G2-S1 | `tests/sphinx_role_guard.py`, `tests/test_sphinx_roles.py` |
| W69-G2-S2 | none |
| W69-G3-S1 | `clockspeed/save/workdir.py`, `tests/save/test_workdir.py` |
| W69-G3-S2 | `docs/adr/0017-the-lane-forks-the-shared-loop-modules.md`, `ops/loop/lanes.py`, `ops/loop/claims.py`, `tests/test_lane_lock.py`, `tests/ops/test_row_claim.py` |
| W70-G1-S1 | `tools/drift_guard.py`, `tests/data/test_item_notes_index.py` |
| W70-G1-S2 | `tests/save/test_reach_guard.py`, `tests/save/reach_guard.py` |
| W70-G2-S1 | `tests/save/test_reference_list.py`, `tests/save/test_reference_pair.py`, `tests/save/test_struct_interior_14_60.py`, `tests/save/test_synthetic.py`, `tests/save/test_trailing_run.py`, `tests/save/test_transform_list.py`, `tests/save/test_world.py` |
| W70-G2-S2 | `tests/data/test_registry.py`, `tests/data/test_version.py`, `clockspeed/data/version.py` |
| W70-G3-S1 | none |
| W70-G3-S2 | `clockspeed/data/locate.py`, `tests/data/test_locate.py` |
| W70-L01 | `tests/test_disposition_sites.py` |
| W71-G1-S1 | `tests/surface/test_aggregate_count_prose.py`, `tests/test_tier1_budget.py` |
| W71-G1-S2 | `tests/save/test_reference_resolution.py`, `tests/save/test_value_anchoring.py`, `tests/save/test_struct_interior.py`, `tests/save/reach_guard.py` |
| W71-G2-S1 | `tests/data/test_item_notes_index.py` |
| W71-G2-S2 | `.claude/commands/done.md` |
| W71-G3-S1 | `clockspeed/save/objects.py`, `tests/save/test_width_rule.py`, `tests/save/test_properties.py` |
| W71-G3-S2 | `tests/sphinx_role_guard.py`, `tests/test_sphinx_roles.py` |
| W72-G1-S1 | `tools/drift_guard.py`, `tools/doc_budget.py`, `tests/data/test_drift_guard_data.py`, `tests/test_doc_budget.py`, `.claude/commands/drift-guard.md`, `tests/shell/test_shell_assets.py` |
| W72-G1-S2 | `tests/test_unregistered_lift.py`, `tests/data/test_drift_guard_skip_names.py`, `tests/data/test_drift_guard_walk_worktree.py`, `tests/surface/test_aggregate_count_prose.py`, `tests/test_doc_sweep.py`, `tests/test_edit_lint_check.py`, `tests/test_freeze_witness.py`, `tests/test_precommit_index_race.py`, `tests/test_provenance_stamp.py`, `tests/test_sha_citation_gate.py` |
| W72-G2-S1 | `tests/conftest.py`, `tests/test_report_redaction_classes.py` |
| W72-G2-S2 | `docs/_archive/` `DATE-cs1295-repo-review-plan-2`, `docs/_archive/` `DATE-cs1295-repo-review-findings-2` |
| W72-G3-S1 | `tests/save/test_byte_order_status.py`, `tests/save/test_properties.py`, `tests/save/test_value_anchoring.py` |
| W72-G3-S2 | `tests/shell/test_shell_assets.py`, `.github/workflows/tier2.yml` |
| W73-G1-S1 | `clockspeed/surface/__main__.py` |
| W73-G1-S2 | `tests/test_exception_rendering.py` |
| W73-L01 | `tests/data/test_phase2_gate.py` |
