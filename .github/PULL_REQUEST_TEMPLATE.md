<!--
This repository reviews on three things: the item, the acceptance conjunct discharged,
and the evidence. Fill those in and delete whatever does not apply. The rules are in
`.github/CONTRIBUTING.md`; the non-negotiables are in `CLAUDE.md`.
-->

## Item

<!-- The CS- id this change belongs to, e.g. CS-000. Write "none - typo" for a
cosmetic fix with no item. Open items are one line in `ROADMAP.md` with their detail
under `docs/item_notes/`. -->

**Item:**

**Headline:** <!-- one line: what this change makes true that was not true before -->

---

## Acceptance conjunct discharged

<!-- Quote the clause from this item's Acceptance section in its
`docs/item_notes/` leaf, and say WHICH conjunct of it this change discharges. An
acceptance clause is a conjunction; discharging one conjunct is progress, not closure. -->

**Quoted clause:**

**Conjunct(s) this change discharges:**

**Conjunct(s) still open after this change:**

---

## Evidence

<!-- Observed this run, not remembered from an earlier one and not predicted. A count
carried forward from a previous run is not evidence. -->

**The failing test came first.** Paste the failure line you saw BEFORE the fix, and say
in one sentence why it was the right reason to fail:

```
```

**The command you ran, and its exit code** - a pipe eats the exit code, so report the
status of the test command itself:

```
```

**Pass/fail counts observed on that run:**

**Tier run** (cosmetic syntax check / this module's tests / full suite), and why that
tier:

---

## Checks

- [ ] 7-bit ASCII only - no em-dash, en-dash or smart quotes, in code, docs and the
      commit message
- [ ] LF line endings only, verified as bytes rather than by a text-mode read
- [ ] Linter and formatter check both clean
- [ ] No co-authorship trailer on any commit - see `docs/GATED.md`, CS-G03
- [ ] No save file, no game data file, and no extracted game asset added to the tree
- [ ] No account name, world name, host name or absolute home-directory path hardcoded
- [ ] No fact restated that another file owns - see `CLAUDE.md` section 4

---

## Anything you could not verify

<!-- State it as unverified. Do not round an uncertainty up to a claim. -->
