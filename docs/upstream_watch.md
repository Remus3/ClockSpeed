# Clockspeed - upstream watch list

**This file owns the upstream watch list for the game's official wiki** - which page
groups a human re-reads when the game updates, and the ORDER that reading happens in.
It is the home CS-486 was filed to find; before it existed the list had no owner in the
topology table, which is the drift `CLAUDE.md` section 4 exists to prevent.

**This file NEVER contains:** lifted upstream content of any kind - no tables, no
datasets, no quoted page bodies, no node lists; the licence verdict (`docs/LEDGER.md`
owns that under CS-485); an item's acceptance criterion (`ROADMAP.md` owns those); or
per-item working detail (`docs/item_notes.md` owns that).

---

## No automated fetch - ever

**NO AUTOMATED FETCH IS EVER NEEDED, AND NONE IS PERMITTED.** Not a poller, not a
scheduled job, not a one-off crawl, not an Action API call, not a raw-wikitext pull. A
human opens the marked pages and reads them.

It is never NEEDED because of the ordering in the next section - the local pin detects
the change, so nothing upstream has to be watched to find out that something moved.

It is not PERMITTED for reasons settled elsewhere and deliberately not restated here:
the licence gate is recorded in `docs/LEDGER.md` under **CS-485**, which holds that
reading a page and citing its URL is CLEARED, that vendoring is REFUSED, and that an
automated poller is forbidden by the platform terms. Read that entry before acting on
anything in this file; do not re-derive its reasoning from this one.

## The ordering IS the point - not the list

**THE INTENDED USE IS THE ORDERING, NOT THE LIST.** The list below is worthless read on
its own schedule and correct read in this sequence:

1. **The local pin fires FIRST.** The game build pin and content hash in
   `clockspeed/data/version.py` are the detector, and `tools/drift_guard.py` is what
   reports that they moved. Nothing upstream is consulted to reach this step.
2. **A human then reads the marked page groups**, to find out WHAT changed - having
   already been told BY THE LOCAL TREE that something did.

That ordering is what keeps this project clear of the crawling clause, the CC
obligations and the authority trap at once, and it is the whole reason no automated
fetch is ever needed.

**Do not invert it.** Reading upstream first to discover that a build moved is the shape
that needs a poller, and the poller is the forbidden thing.

## The page groups

The groups the research pass marked, in the order it named them:

- Patch notes and the version history
- The save-format and blueprint pages
- Milestones
- The MAM
- The space elevator
- The sink
- Clock speed
- Power
- Fuels
- Generators
- Resource nodes
- Transport
- The item and building templates

**Two standing cautions on that list, both already measured and recorded under CS-485.**
Freshness is NOT uniform across it: the patch-notes lane tracks the pinned build while
the save-format lane is a major version behind. And the site's standing is not any
page's authority - the save-format pages carry a byte label this project has already
measured false, so they are watched for CHANGE, never adopted as evidence about save
bytes.

## What this file does NOT record, and how to recover it

**The per-page change signals are not recorded in this repository.** The source block
below describes the list as marking the groups with a per-page change signal, but the
signal for each individual page was never carried into a tracked file - not into this
file's source block, and not into the CS-485 ledger entry, which records the gate result
and the research method and explicitly leaves the list itself homeless.

**THIS IS NOT AN OPEN GAP IN CS-486.** The operator ruled on 2026-08-23 that the page
GROUPS plus the reading order ARE the watch list that item asked for, and CS-486 closed
on that ruling. What follows is a standing note about this file's contents, not an item
state: recovering a per-page signal is worth doing only if someone actually wants one.

**Do not invent them.** Recovering a per-page signal means re-running the CS-485 research
pass - a page-by-page read of the site's navigation and category listings, by a human,
under the ordering above - and recording the result here.

---

## Source of record - relocated VERBATIM

**CS-486 CLOSED 2026-08-23.** The block below WAS written while the item was open and
says so; that sentence was true when written. What is true now: the item is closed,
this file is its home, and THIS FILE IS NOT HISTORY - the watch it describes is
standing, and outlives the item that filed it.

Relocated 2026-08-23 under an operator ruling, from `docs/history_notes.md` under
**CS-486 - detail**, where it had been relocated from `ROADMAP.md` for budget. Verbatim
and not edited. Its closing sentence asks which file should own this list and whether it
belongs under `docs/`; **that decision is the ruling that created this file**, and the
sentence is left standing rather than rewritten.

Relocated from `ROADMAP.md` 2026-08-21 (session 27) for budget, not deleted. The item itself stays OPEN in `ROADMAP.md`. This block is a LIVE instruction, not history.

NOTE: filed 2026-08-19 (session 21). The research is DONE and its gate result is in `docs/LEDGER.md` under CS-485; what is missing is a home, and inventing one mid-ritual would have added a tracked doc with no owner, which is the drift `CLAUDE.md` section 4 exists to prevent. The list marks roughly twenty page groups UPSTREAM with a per-page change signal - patch notes and the version history, the save-format and blueprint pages, milestones, the MAM, the space elevator, the sink, clock speed, power, fuels, generators, resource nodes, transport and the item and building templates. **THE INTENDED USE IS THE ORDERING, NOT THE LIST:** the local build pin plus content hash in `clockspeed/data/version.py` and `tools/drift_guard.py` fire FIRST, and a human then reads the marked pages to find out what changed. That ordering keeps the project clear of the crawling clause, the CC obligations and the authority trap at once, and it means no automated fetch is ever needed. Operator decision still open: which file, and whether it belongs under `docs/`.
