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

## Wave table

| Wave | Group | Slice | Item | Class | Write-list | New files | Landing files | Hub text owed | Lane scope | Milestone | Entry conditions |
|---|---|---|---|---|---|---|---|---|---|---|---|
